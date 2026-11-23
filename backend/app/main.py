from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis import get_redis_pool, close_redis
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

# Mount API Routers
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }
