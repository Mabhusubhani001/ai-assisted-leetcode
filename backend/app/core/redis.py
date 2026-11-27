import uuid
from collections.abc import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

# Global Connection Pool for Redis
_redis_pool: aioredis.ConnectionPool | None = None

def get_redis_pool() -> aioredis.ConnectionPool:
    """Returns or initializes the singleton Redis Connection Pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=True,
        )
    return _redis_pool

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency yielding an async Redis client from the pool."""
    pool = get_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()

async def close_redis() -> None:
    """Closes and releases all connections in the Redis pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None

class TokenGuardrail:
    """
    Real-time atomic guardrail tracking the 2,000-token per-question budget.
    Executes in-memory in RAM to prevent database connection exhaustion under load.
    """
    def __init__(self, redis_client: aioredis.Redis, token_limit: int = settings.QUESTION_TOKEN_LIMIT):
        self.redis = redis_client
        self.token_limit = token_limit

    def _key(self, user_id: str, question_id: uuid.UUID | str) -> str:
        return f"tokens:{user_id}:{question_id}"

    async def get_usage(self, user_id: str, question_id: uuid.UUID | str) -> dict:
        """Fetch current token consumption and locked state."""
        val = await self.redis.get(self._key(user_id, question_id))
        tokens_used = int(val) if val else 0
        return {
            "user_id": user_id,
            "question_id": str(question_id),
            "tokens_used": tokens_used,
            "token_limit": self.token_limit,
            "is_locked": tokens_used >= self.token_limit,
        }

    async def increment_tokens(
        self,
        user_id: str,
        question_id: uuid.UUID | str,
        token_delta: int
    ) -> tuple[int, bool]:
        """
        Atomically increments token consumption using Redis INCRBY.
        Guarantees zero race conditions under concurrent requests.
        Sets 24-hour TTL (86400s) on key so user counters naturally expire daily.
        Returns: (new_total_tokens, is_locked)
        """
        key = self._key(user_id, question_id)
        new_total = await self.redis.incrby(key, token_delta)
        await self.redis.expire(key, 86400)
        is_locked = new_total >= self.token_limit
        return new_total, is_locked

    async def is_locked(self, user_id: str, question_id: uuid.UUID | str) -> bool:
        """Returns True if the student has exceeded the token limit."""
        usage = await self.get_usage(user_id, question_id)
        return usage["is_locked"]

    async def reset(self, user_id: str, question_id: uuid.UUID | str) -> None:
        """Admin override to reset tokens for a given user & question."""
        await self.redis.delete(self._key(user_id, question_id))
