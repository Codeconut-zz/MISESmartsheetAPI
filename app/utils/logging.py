"""Structured logging setup."""

import logging
from typing import Any

import structlog

from app.config import get_settings
from app.utils.redaction import redact


def redact_event_dict(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that redacts sensitive event fields."""
    redacted = redact(event_dict)
    if isinstance(redacted, dict):
        return redacted

    return {"event": "[REDACTED]"}


def setup_logging(log_level: str | None = None) -> None:
    """Configure structlog and stdlib logging."""
    configured_log_level = (log_level or get_settings().log_level).upper()
    logging.basicConfig(level=configured_log_level)

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            redact_event_dict,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
