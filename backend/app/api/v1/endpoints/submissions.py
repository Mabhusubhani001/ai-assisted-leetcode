import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import get_db
from app.core.security import CurrentUser
from app.models.question import Question
from app.models.test_case import TestCase
from app.models.submission import Submission
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    QuestionProgress,
    StudentCatalogSummary,
)
from app.services.code_executor import CodeExecutorService

router = APIRouter(prefix="/submissions", tags=["Code Execution & Submissions"])

DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.post("", response_model=SubmissionResponse)
async def submit_code(
    body: SubmissionCreate,
    current_user: CurrentUser,
    db: DbDep,
):
    """
    Submits code for evaluation against all visible and hidden test cases.
    Transitions through PENDING -> RUNNING -> ACCEPTED / WRONG_ANSWER / TLE.
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

    # 2. Fetch ALL Test Cases (ordered with visible cases first, then hidden cases)
    tc_stmt = (
        select(TestCase)
        .where(TestCase.question_id == question_id)
        .order_by(TestCase.is_hidden.asc(), TestCase.created_at.asc())
    )
    test_cases = list((await db.scalars(tc_stmt)).all())

    if not test_cases:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No test cases configured for this question."
        )

    # Ensure user exists in users table to satisfy foreign key constraint atomically
    user_email = current_user.get("email") or f"{user_id}@example.com"
    user_upsert = (
        pg_insert(User)
        .values(
            id=user_id,
            email=user_email,
            role=current_user.get("role", "student"),
            is_active=True,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    await db.execute(user_upsert)

    # 3. Create initial submission record in PostgreSQL (PENDING)
    submission = Submission(
        user_id=user_id,
        question_id=question_id,
        language_id=body.language_id,
        source_code=body.source_code,
        status="RUNNING",
        total_test_cases=len(test_cases),
        passed_test_cases=0,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # 4. Execute Code via Sandboxed Execution Engine
    exec_result = await CodeExecutorService.execute_submission(
        question=question,
        test_cases=test_cases,
        source_code=body.source_code,
        language_id=body.language_id,
        timeout_sec=question.time_limit_sec,
    )

    # 5. Update submission record with results
    submission.status = exec_result.status
    submission.passed_test_cases = exec_result.passed_test_cases
    submission.total_test_cases = exec_result.total_test_cases
    submission.execution_time_sec = exec_result.execution_time_sec
    submission.memory_used_kb = exec_result.memory_used_kb
    submission.compile_output = exec_result.compile_output
    submission.stderr = exec_result.stderr

    await db.commit()
    await db.refresh(submission)

    # Attach transient execution feedback (failed test case details for public tests)
    response_dto = SubmissionResponse.model_validate(submission)
    response_dto.failed_test_case_info = exec_result.failed_test_case_info

    return response_dto

@router.get("/summary", response_model=StudentCatalogSummary)
async def get_student_catalog_summary(
    current_user: CurrentUser,
    db: DbDep,
):
    """
    Retrieve aggregated submission progress for the authenticated student across all problems.
    Computes SOLVED vs ATTEMPTED status, total counts, and last submitted timestamp.
    """
    user_id = current_user.get("sub")

    stmt = (
        select(
            Submission.question_id,
            func.count(Submission.id).label("attempt_count"),
            func.max(
                case(
                    (Submission.status == "ACCEPTED", 1),
                    else_=0
                )
            ).label("is_solved"),
            func.max(Submission.created_at).label("last_submitted_at"),
        )
        .where(Submission.user_id == user_id)
        .group_by(Submission.question_id)
    )
    rows = (await db.execute(stmt)).all()

    progress = {}
    total_solved = 0
    total_attempted = len(rows)

    for row in rows:
        q_id_str = str(row.question_id)
        solved = bool(row.is_solved)
        if solved:
            total_solved += 1
        progress[q_id_str] = QuestionProgress(
            status="SOLVED" if solved else "ATTEMPTED",
            attempts=row.attempt_count,
            last_submitted_at=row.last_submitted_at,
        )

    return StudentCatalogSummary(
        total_solved=total_solved,
        total_attempted=total_attempted,
        progress=progress,
    )

@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbDep,
):
    """Retrieve full execution status and metrics for a specific submission."""
    submission = await db.scalar(select(Submission).where(Submission.id == submission_id))
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with ID '{submission_id}' not found."
        )

    # Allow access only to submission owner or admin
    user_id = current_user.get("sub")
    if submission.user_id != user_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view another student's submission."
        )

    return submission

@router.get("/history/{question_id}", response_model=list[SubmissionResponse])
async def get_submission_history(
    question_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbDep,
):
    """Retrieve all past submissions by the current student for a given problem."""
    user_id = current_user.get("sub")
    stmt = (
        select(Submission)
        .where(Submission.user_id == user_id, Submission.question_id == question_id)
        .order_by(Submission.created_at.desc())
    )
    result = await db.scalars(stmt)
    return list(result.all())
