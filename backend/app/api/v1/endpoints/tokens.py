import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
import redis.asyncio as aioredis

from app.core.redis import get_redis, TokenGuardrail
from app.schemas.chat import TokenUsageResponse

router = APIRouter(prefix="/tokens", tags=["Token Guardrails"])

RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]

@router.get("/{question_id}", response_model=TokenUsageResponse)
async def get_token_usage(
    question_id: uuid.UUID,
    user_id: Annotated[str, Query(description="Student identifier (Clerk ID)")],
    redis_client: RedisDep,
):
    """
    Check real-time token consumption for a user on a given problem.
    Operates entirely in-memory via Redis.
    """
    guardrail = TokenGuardrail(redis_client)
    usage = await guardrail.get_usage(user_id, question_id)
    return usage

@router.post("/{question_id}/consume", response_model=TokenUsageResponse)
async def consume_tokens(
    question_id: uuid.UUID,
    user_id: Annotated[str, Query(description="Student identifier (Clerk ID)")],
    tokens: Annotated[int, Query(ge=1, le=2000, description="Tokens consumed by prompt/response")],
    redis_client: RedisDep,
):
    """
    Atomically increment token count for a user.
    Simulates token deduction during AI coaching sessions.
    """
    guardrail = TokenGuardrail(redis_client)
    new_total, is_locked = await guardrail.increment_tokens(user_id, question_id, tokens)

    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Token budget of 2,000 exceeded for this problem.",
                "tokens_used": new_total,
                "is_locked": True,
            }
        )

    return {
        "user_id": user_id,
        "question_id": question_id,
        "tokens_used": new_total,
        "token_limit": guardrail.token_limit,
        "is_locked": is_locked,
    }
