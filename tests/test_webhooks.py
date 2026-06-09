from collections.abc import Iterator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api import webhooks
from app.config import Settings
from app.main import app
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base, WebhookEventRecord


def make_client(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with session_scope(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    monkeypatch.setattr(webhooks, "get_settings", lambda: settings)
    client = TestClient(app)
    client.test_engine = engine  # type: ignore[attr-defined]
    return client


def enabled_settings() -> Settings:
    return Settings(
        environment="test",
        enable_webhooks=True,
        webhook_shared_secret="shared-secret",
        _env_file=None,
    )


def test_webhook_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(Settings(environment="test", _env_file=None), monkeypatch)

    response = client.post("/api/v1/webhooks/smartsheet", json={"eventId": "evt-1"})

    assert response.status_code == 404


def test_webhook_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(enabled_settings(), monkeypatch)

    response = client.post("/api/v1/webhooks/smartsheet", json={"eventId": "evt-1"})

    assert response.status_code == 401


def test_webhook_rejects_invalid_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(enabled_settings(), monkeypatch)

    response = client.post(
        "/api/v1/webhooks/smartsheet",
        headers={"X-MISE-Webhook-Secret": "wrong"},
        json={"eventId": "evt-1"},
    )

    assert response.status_code == 403


def test_webhook_accepts_payload_and_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(enabled_settings(), monkeypatch)
    headers = {"X-MISE-Webhook-Secret": "shared-secret"}

    first = client.post("/api/v1/webhooks/smartsheet", headers=headers, json={"eventId": "evt-1"})
    second = client.post("/api/v1/webhooks/smartsheet", headers=headers, json={"eventId": "evt-1"})

    assert first.status_code == 200
    assert first.json() == {"status": "queued", "event_id": "evt-1"}
    assert second.status_code == 200
    assert second.json() == {"status": "duplicate", "event_id": "evt-1"}
    with session_scope(client.test_engine) as session:  # type: ignore[attr-defined]
        assert session.query(WebhookEventRecord).count() == 1
