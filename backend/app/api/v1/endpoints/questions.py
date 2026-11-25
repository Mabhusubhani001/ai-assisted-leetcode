from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.question import Question
from app.models.test_case import TestCase
from app.schemas.question import QuestionListItemResponse, QuestionPublicResponse
from app.schemas.test_case import TestCasePublicResponse

router = APIRouter(prefix="/questions", tags=["Questions & Problem Catalog"])

DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.get("", response_model=list[QuestionListItemResponse])
async def list_questions(db: DbDep):
    """
    List all published DSA assessment questions.
    Returns lightweight summaries for the problem catalog / table.
    """
    stmt = (
        select(Question)
        .where(Question.is_published == True)
        .order_by(Question.created_at)
    )
    result = await db.scalars(stmt)
    return list(result.all())

@router.get("/{slug}", response_model=QuestionPublicResponse)
async def get_question_by_slug(slug: str, db: DbDep):
    """
    Fetch a single question's full details and public test cases by slug.
    
    STRICT SECURITY GUARANTEE:
    Only test cases with is_hidden = False are queried from the database.
    Hidden test cases are NEVER loaded into memory or returned to the client.
    """
    # 1. Fetch Question
    stmt = select(Question).where(Question.slug == slug, Question.is_published == True)
    question = await db.scalar(stmt)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with slug '{slug}' not found."
        )

    # 2. Query strictly visible/public test cases
    tc_stmt = (
        select(TestCase)
        .where(TestCase.question_id == question.id, TestCase.is_hidden == False)
        .order_by(TestCase.created_at)
    )
    public_tcs = await db.scalars(tc_stmt)
    test_cases_list = [TestCasePublicResponse.model_validate(tc) for tc in public_tcs.all()]

    return QuestionPublicResponse(
        id=question.id,
        title=question.title,
        slug=question.slug,
        difficulty=question.difficulty,
        description=question.description,
        starter_code=question.starter_code,
        memory_limit_mb=question.memory_limit_mb,
        time_limit_sec=question.time_limit_sec,
        is_published=question.is_published,
        created_at=question.created_at,
        test_cases=test_cases_list,
    )
