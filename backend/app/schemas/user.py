from pydantic import BaseModel, ConfigDict
import datetime

class UserBase(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str = "student"

class UserResponse(UserBase):
    """Public user response schema."""
    id: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class UserSyncWebhook(BaseModel):
    """Payload received from Clerk webhooks."""
    id: str
    email_addresses: list[dict]
    first_name: str | None = None
    last_name: str | None = None
