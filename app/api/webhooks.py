"""Optional inbound webhook receiver."""

from hashlib import sha256
import json
from secrets import compare_digest
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.config import get_settings
from app.storage.repositories import WebhookEventRepository

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    """Webhook enqueue response."""

    status: str
    event_id: str


@router.post("/smartsheet", response_model=WebhookResponse)
async def receive_smartsheet_webhook(
    request: Request,
    shared_secret: str | None = Header(None, alias="X-MISE-Webhook-Secret"),
    session: Session = Depends(get_db_session),
) -> WebhookResponse:
    """Accept and queue an optional Smartsheet webhook callback."""
    settings = get_settings()
    if not settings.features.enable_webhooks:
        raise HTTPException(status_code=404, detail="Webhook feature is disabled")
    if not settings.security.webhook_shared_secret:
        raise HTTPException(status_code=503, detail="Webhook shared secret is not configured")
    if not shared_secret:
        raise HTTPException(status_code=401, detail="Webhook shared secret header is required")
    if not compare_digest(shared_secret, settings.security.webhook_shared_secret):
        raise HTTPException(status_code=403, detail="Webhook shared secret is invalid")

    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object")

    event_id = _event_id(payload)
    _, created = WebhookEventRepository().enqueue(
        session,
        event_id=event_id,
        source="smartsheet",
        payload=payload,
    )
    return WebhookResponse(status="queued" if created else "duplicate", event_id=event_id)


def _event_id(payload: dict[str, Any]) -> str:
    for key in ("eventId", "event_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)

    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
