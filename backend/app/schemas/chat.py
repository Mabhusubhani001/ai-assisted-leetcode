import uuid
import datetime
from pydantic import BaseModel, ConfigDict, Field

class ChatPromptRequest(BaseModel):
    """Payload sent by student to chat with the AI coaching assistant."""
    question_id: uuid.UUID
    prompt: str = Field(min_length=1, max_length=4000, description="Student approach explanation")

class ChatResponse(BaseModel):
    """Chat log record schema."""
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
    """Real-time token budget query schema (pulled from Redis)."""
    user_id: str
    question_id: uuid.UUID
    tokens_used: int
    token_limit: int = 2000
    is_locked: bool
