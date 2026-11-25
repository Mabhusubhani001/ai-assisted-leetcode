from fastapi import APIRouter
from app.api.v1.endpoints import (
    tokens,
    webhooks,
    auth,
    questions,
    chat,
    submissions,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(questions.router)
api_router.include_router(chat.router)
api_router.include_router(submissions.router)
api_router.include_router(tokens.router)
api_router.include_router(webhooks.router)
api_router.include_router(auth.router)
