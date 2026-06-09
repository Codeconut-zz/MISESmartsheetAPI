"""Utilities for removing sensitive values from log output."""

from collections.abc import Mapping, Sequence
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

MASK = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
LONG_ID_PATTERN = re.compile(r"\b(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{16,}\b")
BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
KEY_VALUE_PATTERN = re.compile(
    r"(?i)\b(password|token|secret|api[_-]?key|authorization)=([^&\s]+)"
)


def redact(value: Any) -> Any:
    """Recursively redact sensitive data while preserving the original shape."""
    if isinstance(value, Mapping):
        return {
            key: MASK if _is_sensitive_key(str(key)) else redact(nested_value)
            for key, nested_value in value.items()
        }

    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)

    if _is_sequence(value):
        return [redact(item) for item in value]

    if isinstance(value, str):
        return redact_text(value)

    return value


def redact_text(text: str) -> str:
    """Mask sensitive patterns in free-form text."""
    redacted = _redact_url_password(text)
    redacted = BEARER_PATTERN.sub("Bearer " + MASK, redacted)
    redacted = KEY_VALUE_PATTERN.sub(lambda match: f"{match.group(1)}={MASK}", redacted)
    redacted = EMAIL_PATTERN.sub(MASK, redacted)
    return LONG_ID_PATTERN.sub(MASK, redacted)


def _is_sensitive_key(key: str) -> bool:
    normalized_key = key.lower()
    return any(part in normalized_key for part in SENSITIVE_KEY_PARTS)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _redact_url_password(text: str) -> str:
    if "://" not in text:
        return text

    try:
        parsed = urlsplit(text)
    except ValueError:
        return text

    if not parsed.password or not parsed.hostname:
        return text

    username = parsed.username or ""
    hostname = parsed.hostname
    port = f":{parsed.port}" if parsed.port else ""
    auth = f"{username}:{MASK}@" if username else ""
    netloc = f"{auth}{hostname}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
