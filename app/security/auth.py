"""JWT bearer authentication and role authorization."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import hmac
import json
from typing import Any, Literal

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.config import Settings, get_settings

Role = Literal["admin", "reporting", "read_only", "integration_service"]
ALL_ROLES: set[str] = {"admin", "reporting", "read_only", "integration_service"}


class AuthenticatedUser(BaseModel):
    """Authenticated API caller."""

    model_config = ConfigDict(frozen=True)

    subject: str
    roles: set[str] = Field(default_factory=set)


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """Return the authenticated user from a bearer JWT."""
    if _auth_bypass_enabled(settings):
        return AuthenticatedUser(subject="development-bypass", roles=set(ALL_ROLES))

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not settings.security.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT authentication is not configured",
        )

    payload = decode_jwt(authorization.removeprefix("Bearer ").strip(), settings.security.jwt_secret)
    roles = payload.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    return AuthenticatedUser(
        subject=str(payload.get("sub") or ""),
        roles={str(role) for role in roles},
    )


def require_roles(*allowed_roles: Role) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Return a dependency that requires at least one allowed role."""

    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        return user

    return dependency


def decode_jwt(token: str, secret: str) -> dict[str, Any]:
    """Decode and verify a compact HS256 JWT."""
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise _unauthorized("Invalid bearer token") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = _sign(signing_input, secret)
    actual_signature = _base64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise _unauthorized("Invalid bearer token")

    header = _json_segment(header_segment)
    if header.get("alg") != "HS256":
        raise _unauthorized("Unsupported JWT algorithm")

    payload = _json_segment(payload_segment)
    exp = payload.get("exp")
    if exp is not None and int(exp) < int(datetime.now(UTC).timestamp()):
        raise _unauthorized("Bearer token expired")

    return payload


def encode_jwt(payload: dict[str, Any], secret: str) -> str:
    """Encode a compact HS256 JWT for tests and local tooling."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = _base64url_json(header)
    payload_segment = _base64url_json(payload)
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature_segment = _base64url_encode(_sign(signing_input, secret))
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def _auth_bypass_enabled(settings: Settings) -> bool:
    return settings.environment == "development" and settings.security.auth_disabled


def _json_segment(segment: str) -> dict[str, Any]:
    try:
        payload = json.loads(_base64url_decode(segment))
    except (ValueError, json.JSONDecodeError) as exc:
        raise _unauthorized("Invalid bearer token") from exc
    if not isinstance(payload, dict):
        raise _unauthorized("Invalid bearer token")

    return payload


def _base64url_json(payload: dict[str, Any]) -> str:
    return _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def _base64url_encode(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(f"{value}{padding}")


def _sign(signing_input: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
