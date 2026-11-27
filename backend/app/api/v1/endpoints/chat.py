import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
import redis.asyncio as aioredis

from app.core.database import get_db, AsyncSessionLocal
from app.core.redis import get_redis, TokenGuardrail
from app.core.security import CurrentUser
from app.models.question import Question
from app.models.chat_log import ChatLog
from app.models.user import User
from app.schemas.chat import (
    ChatPromptRequest,
    ChatEvaluationResponse,
    ChatResponse,
)
from app.services.ai_coach import AICoachService
from app.services.llm_coach import LLMCoachService

router = APIRouter(prefix="/chat", tags=["AI Coaching & Approach Validation"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]

async def persist_chat_log(
    user_id: str,
    question_id: uuid.UUID,
    prompt: str,
    response: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
):
    """
    Non-blocking background worker that persists chat logs to PostgreSQL.
    Prevents database transaction latency from delaying the AI response to the student.
    Auto-provisions user row if missing (e.g. dev accounts or webhook race conditions).
    """
    async with AsyncSessionLocal() as session:
        # Ensure user exists to satisfy foreign key constraint atomically
        user_upsert = (
            pg_insert(User)
            .values(
                id=user_id,
                email=f"{user_id}@example.com",
                role="student",
                is_active=True,
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await session.execute(user_upsert)

        log = ChatLog(
            user_id=user_id,
            question_id=question_id,
            prompt=prompt,
            response=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        session.add(log)
        await session.commit()

@router.post("/message", response_model=ChatEvaluationResponse)
async def evaluate_approach(
    body: ChatPromptRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: DbDep,
    redis_client: RedisDep,
):
    """
    AI Coaching endpoint that evaluates the student's algorithmic approach.
    Enforces prompt injection defense, time/space complexity checks, and data structure verification.
    Unlocks the code editor when all criteria are met.
    """
    user_id = current_user.get("sub")
    question_id = body.question_id

    # 1. Fetch Question
    question = await db.scalar(select(Question).where(Question.id == question_id))
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found."
        )

    # 2. Redis Guardrail: Check if already locked (budget exceeded)
    guardrail = TokenGuardrail(redis_client)
    if await guardrail.is_locked(user_id, question_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token budget of 2,000 exceeded for this problem. The AI Coach is locked."
        )

    # 3. Retrieve Multi-Turn Conversational Memory from Database
    recent_logs = await db.scalars(
        select(ChatLog)
        .where(ChatLog.user_id == user_id, ChatLog.question_id == question_id)
        .order_by(ChatLog.created_at.asc())
        .limit(20)
    )
    conversation_history: list[dict[str, str]] = []
    for log in recent_logs:
        conversation_history.append({"role": "user", "content": log.prompt})
        conversation_history.append({"role": "assistant", "content": log.response})

    # 4. Evaluate Approach via Multi-Turn LLM Coach Service (Featherless default / Gemini / Claude BYOK)
    eval_result = await LLMCoachService.evaluate_with_history(
        question=question,
        current_prompt=body.prompt,
        conversation_history=conversation_history,
        language=body.language,
        custom_provider=body.custom_provider,
        custom_api_key=body.custom_api_key,
        custom_model=body.custom_model,
    )

    # 5. Atomic Token Deduction in Redis
    new_total, is_locked = await guardrail.increment_tokens(
        user_id=user_id,
        question_id=question_id,
        token_delta=eval_result.tokens_consumed
    )

    # 6. Non-blocking Background Persistence to PostgreSQL
    background_tasks.add_task(
        persist_chat_log,
        user_id=user_id,
        question_id=question_id,
        prompt=body.prompt,
        response=eval_result.feedback,
        prompt_tokens=eval_result.prompt_tokens,
        completion_tokens=eval_result.completion_tokens,
        total_tokens=eval_result.tokens_consumed,
    )

    return ChatEvaluationResponse(
        is_approved=eval_result.is_approved,
        feedback=eval_result.feedback,
        detected_data_structure=eval_result.detected_data_structure,
        detected_algorithm=eval_result.detected_algorithm,
        time_complexity=eval_result.time_complexity,
        space_complexity=eval_result.space_complexity,
        missing_requirements=eval_result.missing_requirements,
        starter_code=eval_result.starter_code,
        prompt_tokens=eval_result.prompt_tokens,
        completion_tokens=eval_result.completion_tokens,
        turn_tokens=eval_result.turn_tokens,
        tokens_consumed=eval_result.tokens_consumed,
        tokens_used=new_total,
        token_limit=guardrail.token_limit,
        is_locked=is_locked,
        provider_used=eval_result.provider_used,
        model_used=eval_result.model_used,
    )

@router.get("/history/{question_id}", response_model=list[ChatResponse])
async def get_chat_history(
    question_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbDep,
):
    """
    Retrieve historical AI coaching interactions for the current student on this problem.
    """
    user_id = current_user.get("sub")
    stmt = (
        select(ChatLog)
        .where(ChatLog.user_id == user_id, ChatLog.question_id == question_id)
        .order_by(ChatLog.created_at.asc())
    )
    result = await db.scalars(stmt)
    return list(result.all())
