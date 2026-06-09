from collections.abc import Iterator

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.config import Settings, get_settings
from app.main import app
from app.security.auth import encode_jwt
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base

JWT_SECRET = "test-jwt-secret"


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def make_client(settings: Settings) -> TestClient:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with session_scope(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def auth_header(*roles: str) -> dict[str, str]:
    token = encode_jwt({"sub": "tester", "roles": list(roles)}, JWT_SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_api_endpoint_rejects_missing_bearer_token() -> None:
    client = make_client(Settings(environment="test", jwt_secret=JWT_SECRET, _env_file=None))

    response = client.get("/api/v1/reports/summary")

    assert response.status_code == 401


def test_api_endpoint_allows_authorized_reporting_role() -> None:
    client = make_client(Settings(environment="test", jwt_secret=JWT_SECRET, _env_file=None))

    response = client.get("/api/v1/reports/summary", headers=auth_header("reporting"))

    assert response.status_code == 200
    assert "summary" in response.json()


def test_api_endpoint_rejects_insufficient_role() -> None:
    client = make_client(Settings(environment="test", jwt_secret=JWT_SECRET, _env_file=None))

    response = client.get("/api/v1/reports/summary", headers=auth_header("integration_service"))

    assert response.status_code == 403


def test_development_auth_bypass_requires_development_environment() -> None:
    client = make_client(
        Settings(
            environment="development",
            auth_disabled=True,
            _env_file=None,
        )
    )

    response = client.get("/api/v1/reports/summary")

    assert response.status_code == 200


def test_production_rejects_auth_disabled() -> None:
    with pytest.raises(ValidationError, match="AUTH_DISABLED"):
        Settings(
            environment="production",
            auth_disabled=True,
            jwt_secret=JWT_SECRET,
            smartsheet_access_token="token",
            smartsheet_tir_sheet_id="sheet",
            database_url="postgresql+psycopg2://mise:secure@db.example.test:5432/mise",
            mise_project_root="C:/MISE/projects",
            mise_registry_root="C:/MISE/registry",
            _env_file=None,
        )
