import json
from typing import Annotated
from fastapi import APIRouter, Request, Header, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    db: DbDep,
    svix_id: Annotated[str | None, Header(alias="svix-id")] = None,
    svix_timestamp: Annotated[str | None, Header(alias="svix-timestamp")] = None,
    svix_signature: Annotated[str | None, Header(alias="svix-signature")] = None,
):
    """
    Svix-verified Clerk Webhook endpoint.
    Syncs user.created, user.updated, and user.deleted events directly to PostgreSQL.
    """
    raw_body = await request.body()

    # In production, require svix signature headers
    if not svix_id or not svix_timestamp or not svix_signature:
        # In development, allow raw payload if no secret configured
        if settings.ENVIRONMENT != "development" or settings.CLERK_WEBHOOK_SECRET != "whsec_local_test_key":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Svix verification headers."
            )

    # Cryptographic signature verification via Svix
    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        headers = {
            "svix-id": svix_id or "test-id",
            "svix-timestamp": svix_timestamp or "0",
            "svix-signature": svix_signature or "test-sig"
        }
        # If valid secret and headers provided, verify
        if svix_signature:
            wh.verify(raw_body, headers)
    except WebhookVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {str(e)}"
        )

    # Parse verified payload
    payload = json.loads(raw_body.decode("utf-8"))
    event_type = payload.get("type")
    data = payload.get("data", {})
    user_id = data.get("id")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user ID in payload.")

    # 1. Handle user.created
    if event_type == "user.created":
        email_addresses = data.get("email_addresses", [])
        primary_email = email_addresses[0]["email_address"] if email_addresses else f"{user_id}@noemail.com"
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        # Check if user already exists
        existing = await db.scalar(select(User).where(User.id == user_id))
        if not existing:
            new_user = User(
                id=user_id,
                email=primary_email,
                first_name=first_name,
                last_name=last_name,
                role="student",
                is_active=True,
            )
            db.add(new_user)
            await db.commit()
            return {"status": "success", "event": "user.created", "user_id": user_id}

    # 2. Handle user.updated
    elif event_type == "user.updated":
        existing = await db.scalar(select(User).where(User.id == user_id))
        if existing:
            email_addresses = data.get("email_addresses", [])
            if email_addresses:
                existing.email = email_addresses[0]["email_address"]
            existing.first_name = data.get("first_name", existing.first_name)
            existing.last_name = data.get("last_name", existing.last_name)
            await db.commit()
            return {"status": "success", "event": "user.updated", "user_id": user_id}

    # 3. Handle user.deleted (Soft Delete per ADR-005)
    elif event_type == "user.deleted":
        existing = await db.scalar(select(User).where(User.id == user_id))
        if existing:
            existing.is_active = False
            await db.commit()
            return {"status": "success", "event": "user.deleted", "user_id": user_id, "is_active": False}

    return {"status": "ignored", "event": event_type}
