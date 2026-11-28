from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "leetcode_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leetcode_db"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Guardrails
    QUESTION_TOKEN_LIMIT: int = 2000

    # LLM Provider Configuration (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_PRIMARY_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.1-flash-lite",
        "gemini-4-hydrogen",
    ]

    # Clerk Authentication & Webhook Sync
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = "pk_test_dG9waWNhbC1wcmF3bi0xNjcuY2xlcmsuYWNjb3VudHMuZGV2JA"
    CLERK_WEBHOOK_SECRET: str = "whsec_local_test_key"
    CLERK_JWKS_URL: str = "https://topical-prawn-167.clerk.accounts.dev/.well-known/jwks.json"
    CLERK_PEM_PUBLIC_KEY: str = ""

    # Judge0 Sandboxed Execution Configuration (Self-Hosted on EC2 or RapidAPI)
    JUDGE0_API_URL: str = ""  # e.g. "http://judge0.internal:2358" or "https://judge0-ce.p.rapidapi.com"
    JUDGE0_AUTH_TOKEN: str = ""  # Optional auth token for self-hosted Judge0
    JUDGE0_RAPIDAPI_KEY: str = ""  # Optional RapidAPI key if using managed Judge0
    JUDGE0_RAPIDAPI_HOST: str = "judge0-ce.p.rapidapi.com"

    # Admin CLI & Portal Secret Key
    ADMIN_API_KEY: str = "dsa_admin_secret_key_change_in_prod"

    # CORS Allowed Origins
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://dsa.msdevs.mooo.com",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore"
    )

settings = Settings()
