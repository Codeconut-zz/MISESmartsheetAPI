import pytest
from pydantic import ValidationError

from app.config import (
    ALLOWED_EXPORT_FORMATS,
    DEFAULT_REPORT_FOLDERS,
    AppSettings,
    DatabaseSettings,
    FeatureFlags,
    FilesystemSettings,
    SecuritySettings,
    Settings,
    SmartsheetSettings,
    get_settings,
)


def test_settings_load_in_test_mode() -> None:
    settings = Settings(environment="test", _env_file=None)

    assert settings.environment == "test"
    assert settings.enable_write_operations is False
    assert settings.require_apply_flag is True


def test_development_settings_have_grouped_views() -> None:
    settings = Settings(_env_file=None)

    assert isinstance(settings.app, AppSettings)
    assert isinstance(settings.smartsheet, SmartsheetSettings)
    assert isinstance(settings.database, DatabaseSettings)
    assert isinstance(settings.filesystem, FilesystemSettings)
    assert isinstance(settings.security, SecuritySettings)
    assert isinstance(settings.features, FeatureFlags)
    assert settings.app.environment == "development"
    assert settings.smartsheet.base_url == "https://api.smartsheet.com/2.0"
    assert settings.database.url.startswith("postgresql+psycopg2://")
    assert settings.filesystem.report_export_root in DEFAULT_REPORT_FOLDERS
    assert "xlsx" in ALLOWED_EXPORT_FORMATS


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()

    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings
    get_settings.cache_clear()


def test_production_requires_operational_values() -> None:
    with pytest.raises(ValidationError, match="SMARTSHEET_ACCESS_TOKEN"):
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


def test_production_like_settings_load_with_required_values() -> None:
    settings = Settings(
        environment="production",
        smartsheet_access_token="token-value",
        smartsheet_tir_sheet_id="sheet-123",
        database_url="postgresql+psycopg2://mise:secure@db.example.test:5432/mise",
        mise_project_root="C:/MISE/projects",
        mise_registry_root="C:/MISE/registry",
        report_export_root="C:/MISE/reports",
        enable_write_operations=False,
        require_apply_flag=True,
        _env_file=None,
    )

    assert settings.app.environment == "production"
    assert settings.smartsheet.access_token == "token-value"
    assert settings.database.url.endswith("/mise")
