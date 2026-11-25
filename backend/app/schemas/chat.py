import uuid
import datetime
from pydantic import BaseModel, ConfigDict, Field

class ChatPromptRequest(BaseModel):
    """Payload sent by student to explain their algorithmic approach."""
    question_id: uuid.UUID
    prompt: str = Field(min_length=1, max_length=4000, description="Student approach explanation")
    language: str = Field(default="python", description="Target programming language for starter code")
    custom_provider: str | None = Field(default=None, description="Optional BYOK provider (featherless, gemini, claude)")
    custom_api_key: str | None = Field(default=None, description="Optional user-supplied API key")
    custom_model: str | None = Field(default=None, description="Optional custom model override")

class ChatEvaluationResponse(BaseModel):
    """Rich evaluation returned by the AI Coach."""
    is_approved: bool
    feedback: str
    detected_data_structure: str | None = None
    detected_algorithm: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    missing_requirements: list[str] = []
    starter_code: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    turn_tokens: int = 0
    tokens_consumed: int
    tokens_used: int
    token_limit: int = 2000
    is_locked: bool
    provider_used: str = "gemini"
    model_used: str = "gemini-3.5-flash-lite"

class ChatResponse(BaseModel):
    """Historical chat log item."""
    id: uuid.UUID
    user_id: str
    question_id: uuid.UUID
    prompt: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class TokenUsageResponse(BaseModel):
    """Real-time token budget query schema."""
    user_id: str
    question_id: uuid.UUID
    tokens_used: int
    token_limit: int = 2000
    is_locked: bool
