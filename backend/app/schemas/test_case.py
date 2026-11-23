import uuid
from pydantic import BaseModel, ConfigDict

class TestCaseBase(BaseModel):
    stdin: str
    expected_stdout: str

class TestCaseCreate(TestCaseBase):
    """Admin schema for creating test cases."""
    is_hidden: bool = False

class TestCasePublicResponse(TestCaseBase):
    """
    STRICT SECURITY BOUNDARY:
    Only public test cases are serialized through this schema.
    The 'is_hidden' column is NOT exposed here.
    """
    id: uuid.UUID
    question_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class TestCaseInternal(TestCaseBase):
    """Used strictly by internal Judge0 execution workers."""
    id: uuid.UUID
    question_id: uuid.UUID
    is_hidden: bool

    model_config = ConfigDict(from_attributes=True)
