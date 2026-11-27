from typing import Annotated
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# HTTP Bearer scheme (extracts Bearer <token>)
security_scheme = HTTPBearer(auto_error=True)

# In-memory JWKS client if JWKS URL is configured
_jwks_client: PyJWKClient | None = None

def get_jwks_client() -> PyJWKClient | None:
    global _jwks_client
    if _jwks_client is None and settings.CLERK_JWKS_URL:
        _jwks_client = PyJWKClient(settings.CLERK_JWKS_URL, cache_jwk_set=True, lifespan=86400)
    return _jwks_client

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)]
) -> dict:
    """
    Verifies Clerk Session JWT and returns user payload.
    Uses cached asymmetric JWKS / PEM public key in RAM (<1ms verification).
    """
    token = credentials.credentials

    # Development convenience: Allow simulated dev tokens for offline testing
    if settings.ENVIRONMENT == "development" and token.startswith("dev_user_"):
        return {
            "sub": token,
            "email": f"{token}@example.com",
            "role": "student"
        }

    try:
        # Verify via PEM public key if provided
        if settings.CLERK_PEM_PUBLIC_KEY:
            payload = jwt.decode(
                token,
                settings.CLERK_PEM_PUBLIC_KEY,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            return payload

        # Verify via Clerk JWKS endpoint
        jwks_client = get_jwks_client()
        if jwks_client is not None:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            return payload

        # If no public key is configured yet in local development, decode unverified with warning
        if settings.ENVIRONMENT == "development":
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk public keys (JWKS or PEM) not configured on backend."
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

CurrentUser = Annotated[dict, Depends(get_current_user)]

# Optional bearer authentication scheme for endpoints with dual/flexible auth
security_scheme_optional = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme_optional)] = None
) -> dict | None:
    """
    Extracts and validates Clerk JWT if provided in Bearer header.
    Returns None if missing or invalid instead of throwing HTTP 401 immediately.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def require_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    current_user: Annotated[dict | None, Depends(get_current_user_optional)] = None,
) -> dict:
    """
    Dual-auth administrative security dependency:
    1. Header 'X-Admin-Key': Direct machine/CLI access using ADMIN_API_KEY.
    2. Clerk Session JWT: User with role == 'admin' in claims or metadata.
    """
    if x_admin_key and x_admin_key == settings.ADMIN_API_KEY:
        return {"sub": "admin_cli", "role": "admin"}

    if current_user:
        role = current_user.get("role") or current_user.get("public_metadata", {}).get("role")
        if role == "admin":
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required: provide valid X-Admin-Key header or Clerk admin credentials."
    )
