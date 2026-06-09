"""Audit event domain model."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Environment
from app.utils.redaction import redact, redact_text

AuditStatus = Literal["success", "failure", "warning", "pending"]


class AuditEvent(BaseModel):
    """Structured record of an auditable application action."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str
    action: str
    target_type: str
    target_id: str
    environment: Environment
    dry_run: bool
    status: AuditStatus
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message", mode="before")
    @classmethod
    def redact_message(cls, value: Any) -> str:
        """Redact sensitive text before the event is stored."""
        return redact_text(str(value))

    @field_validator("metadata", mode="before")
    @classmethod
    def redact_metadata(cls, value: Any) -> dict[str, Any]:
        """Redact sensitive metadata before the event is stored."""
        if not isinstance(value, dict):
            return {}

        redacted = redact(value)
        if isinstance(redacted, dict):
            return redacted

        return {}
