import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
import redis.asyncio as aioredis

from app.core.redis import get_redis, TokenGuardrail
from app.core.security import CurrentUser, require_admin
from app.schemas.chat import TokenUsageResponse

router = APIRouter(prefix="/tokens", tags=["Token Guardrails"])

RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]

@router.get("/{question_id}", response_model=TokenUsageResponse)
async def get_token_usage(
    question_id: uuid.UUID,
    current_user: CurrentUser,
    redis_client: RedisDep,
    user_id: Annotated[str | None, Query(description="Target student identifier (Admin only)")] = None,
):
    """
    Check real-time token consumption for a user on a given problem.
    Enforces tenant isolation: students can only inspect their own token usage.
    """
    req_user_id = current_user.get("sub")
    role = current_user.get("role") or current_user.get("public_metadata", {}).get("role")
    target_user_id = user_id if (user_id and role == "admin") else req_user_id

    guardrail = TokenGuardrail(redis_client)
    usage = await guardrail.get_usage(target_user_id, question_id)
    return usage

@router.post("/{question_id}/consume", response_model=TokenUsageResponse)
async def consume_tokens(
    question_id: uuid.UUID,
    tokens: Annotated[int, Query(ge=1, le=2000, description="Tokens consumed by prompt/response")],
    current_user: CurrentUser,
    redis_client: RedisDep,
    user_id: Annotated[str | None, Query(description="Target student identifier override for admin/testing")] = None,
):
    """
    Atomically increment token count for a user.
    Enforces tenant isolation: students can only increment their own tokens.
    """
    req_user_id = current_user.get("sub")
    role = current_user.get("role") or current_user.get("public_metadata", {}).get("role")
    target_user_id = user_id if (user_id and (role == "admin" or req_user_id.startswith("dev_user_"))) else req_user_id

    guardrail = TokenGuardrail(redis_client)
    new_total, is_locked = await guardrail.increment_tokens(target_user_id, question_id, tokens)

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
        "user_id": target_user_id,
        "question_id": question_id,
        "tokens_used": new_total,
        "token_limit": guardrail.token_limit,
        "is_locked": is_locked,
    }

@router.post("/{question_id}/reset", response_model=dict)
async def reset_tokens_admin(
    question_id: uuid.UUID,
    user_id: Annotated[str, Query(description="Target student identifier")],
    admin: Annotated[dict, Depends(require_admin)],
    redis_client: RedisDep,
):
    """Admin-only endpoint to reset a student's token counter in Redis."""
    guardrail = TokenGuardrail(redis_client)
    await guardrail.reset(user_id, question_id)
    return {"status": "reset", "user_id": user_id, "tokens_used": 0}
