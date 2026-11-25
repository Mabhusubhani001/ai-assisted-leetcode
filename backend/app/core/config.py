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
    GEMINI_PRIMARY_MODEL: str = "gemini-3.8-flash"
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]

    # Clerk Authentication & Webhook Sync
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = "whsec_local_test_key"
    CLERK_JWKS_URL: str = ""
    CLERK_PEM_PUBLIC_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore"
    )

settings = Settings()
