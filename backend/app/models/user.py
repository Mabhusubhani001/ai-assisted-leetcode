from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.chat_log import ChatLog

class User(Base, TimestampMixin):
    """
    Users table synced with Clerk Identity Provider.
    Primary Key matches Clerk user ID (e.g. 'user_2xyz...').
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        doc="Clerk User ID"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20),
        default="student",
        nullable=False,
        doc="Role: 'student' or 'admin'"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Soft delete flag for Clerk user.deleted webhook"
    )

    # Relationships
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="user")
    chat_logs: Mapped[list["ChatLog"]] = relationship("ChatLog", back_populates="user")
