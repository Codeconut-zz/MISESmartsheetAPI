import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_load_in_test_mode() -> None:
    settings = Settings(environment="test", _env_file=None)

    assert settings.environment == "test"
    assert settings.enable_write_operations is False
    assert settings.require_apply_flag is True


def test_production_requires_operational_values() -> None:
    with pytest.raises(ValidationError, match="Production settings missing required values"):
        Settings(environment="production", _env_file=None)


def test_production_rejects_placeholder_database_url() -> None:
    with pytest.raises(ValidationError, match="example local placeholder"):
        Settings(
            environment="production",
            smartsheet_access_token="token-value",
            smartsheet_tir_sheet_id="sheet-id",
            mise_project_root="C:/MISE/projects",
            mise_registry_root="C:/MISE/registry",
            _env_file=None,
        )
