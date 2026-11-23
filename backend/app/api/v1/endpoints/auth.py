from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import CurrentUser
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the database profile of the currently authenticated Clerk user.
    Demonstrates end-to-end Bearer JWT authorization and DB query.
    """
    user_id = current_user.get("sub")
    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        # Fallback profile if user hasn't synced via webhook yet
        return UserResponse(
            id=user_id,
            email=current_user.get("email", f"{user_id}@clerk.dev"),
            first_name=current_user.get("first_name"),
            last_name=current_user.get("last_name"),
            role=current_user.get("role", "student"),
            is_active=True,
            created_at=current_user.get("created_at") or "2026-11-23T00:00:00Z"
        )

    return user
