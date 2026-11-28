import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis import get_redis_pool, close_redis, get_redis
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    Pre-warms connections and ensures graceful termination.
    """
    # Startup: Verify Redis connection
    pool = get_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        await client.ping()
    finally:
        await client.aclose()

    yield

    # Shutdown: Close Redis connection pool
    await close_redis()

app = FastAPI(
    title="AI-Assisted DSA Assessment Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS with strict origin whitelisting (no arbitrary wildcard regex)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router)

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }

# ACME token format according to RFC 8555: base64url characters (A-Z, a-z, 0-9, -, _)
ACME_TOKEN_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

@app.get("/.well-known/acme-challenge/{token}")
async def acme_challenge(
    token: str,
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    RFC 8555 HTTP-01 challenge responder for Let's Encrypt / ACME validation.
    Reads pre-authorized token responses from Redis to avoid filesystem writes
    and prevent path traversal vulnerabilities.
    """
    if not ACME_TOKEN_REGEX.match(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ACME challenge token format",
        )
    val = await redis.get(f"acme:{token}")
    if val:
        return Response(content=val, media_type="text/plain")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="ACME challenge token not found",
    )
