import uuid
import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

SubmissionStatus = Literal[
    "PENDING",
    "RUNNING",
    "ACCEPTED",
    "WRONG_ANSWER",
    "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED",
    "COMPILATION_ERROR",
    "RUNTIME_ERROR",
    "INTERNAL_ERROR"
]

class SubmissionCreate(BaseModel):
    """Payload sent by student to execute/submit code."""
    question_id: uuid.UUID
    language_id: int = Field(description="Judge0 language ID (e.g. 71 for Python, 63 for JavaScript)")
    source_code: str = Field(min_length=1, max_length=65536, description="Student solution source code")

class SubmissionResponse(BaseModel):
    """Submission result returned to client."""
    id: uuid.UUID
    user_id: str
    question_id: uuid.UUID
    language_id: int
    source_code: str
    status: SubmissionStatus
    execution_time_sec: float | None = None
    memory_used_kb: int | None = None
    compile_output: str | None = None
    stderr: str | None = None
    passed_test_cases: int
    total_test_cases: int
    failed_test_case_info: dict | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class QuestionProgress(BaseModel):
    status: Literal["SOLVED", "ATTEMPTED"]
    attempts: int
    last_submitted_at: datetime.datetime

class StudentCatalogSummary(BaseModel):
    total_solved: int
    total_attempted: int
    progress: dict[str, QuestionProgress]

