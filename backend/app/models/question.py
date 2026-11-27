import uuid
from sqlalchemy import String, Text, Integer, Float, Boolean, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.test_case import TestCase
    from app.models.submission import Submission
    from app.models.chat_log import ChatLog

class Question(Base, TimestampMixin):
    """
    Coding assessment problems.
    Uses UUID PK and slug for URL routing.
    """
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4()
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # easy, medium, hard
    description: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown
    starter_code: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    driver_code: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    time_limit_sec: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    test_cases: Mapped[list["TestCase"]] = relationship("TestCase", back_populates="question", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="question", cascade="all, delete-orphan")
    chat_logs: Mapped[list["ChatLog"]] = relationship("ChatLog", back_populates="question", cascade="all, delete-orphan")
