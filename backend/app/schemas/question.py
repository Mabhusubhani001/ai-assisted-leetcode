import uuid
import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from app.schemas.test_case import TestCasePublicResponse

DifficultyType = Literal["easy", "medium", "hard"]

class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    difficulty: DifficultyType
    description: str = Field(description="Markdown description of the problem")
    starter_code: dict[str, str] = Field(default_factory=dict, description="Starter code keyed by language")
    memory_limit_mb: int = Field(default=256, ge=16, le=1024)
    time_limit_sec: float = Field(default=2.0, ge=0.1, le=10.0)

class QuestionCreate(QuestionBase):
    """Schema used by admins to create questions."""
    is_published: bool = False

class QuestionPublicResponse(QuestionBase):
    """
    Public question detail schema for students.
    Only exposes public (visible) test cases for practice.
    """
    id: uuid.UUID
    is_published: bool
    created_at: datetime.datetime
    test_cases: list[TestCasePublicResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class QuestionListItemResponse(BaseModel):
    """Lightweight schema for problem listings / catalog."""
    id: uuid.UUID
    title: str
    slug: str
    difficulty: DifficultyType
    is_published: bool

    model_config = ConfigDict(from_attributes=True)
