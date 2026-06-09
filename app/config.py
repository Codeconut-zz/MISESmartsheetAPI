"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
ExportFormat = Literal["csv", "xlsx", "json"]

DEFAULT_REPORT_FOLDER = "data/reports"
DEFAULT_EXPORT_FOLDER = "data/exports"
DEFAULT_REPORT_FOLDERS = (DEFAULT_REPORT_FOLDER, DEFAULT_EXPORT_FOLDER)
ALLOWED_EXPORT_FORMATS: frozenset[ExportFormat] = frozenset(("csv", "xlsx", "json"))

REQUIRED_PRODUCTION_FIELDS = (
    ("SMARTSHEET_ACCESS_TOKEN", "smartsheet_access_token"),
    ("SMARTSHEET_TIR_SHEET_ID", "smartsheet_tir_sheet_id"),
    ("DATABASE_URL", "database_url"),
    ("MISE_PROJECT_ROOT", "mise_project_root"),
    ("MISE_REGISTRY_ROOT", "mise_registry_root"),
)


class FrozenSettingsModel(BaseModel):
    """Base model for immutable grouped settings."""

    model_config = ConfigDict(frozen=True)


class AppSettings(FrozenSettingsModel):
    """Application runtime settings."""

    environment: Environment
    log_level: str


class SmartsheetSettings(FrozenSettingsModel):
    """Smartsheet API settings."""

    base_url: str
    access_token: str
    tir_sheet_id: str


class DatabaseSettings(FrozenSettingsModel):
    """Database connection settings."""

    url: str


class FilesystemSettings(FrozenSettingsModel):
    """Local filesystem settings."""

    mise_project_root: str
    mise_registry_root: str
    report_export_root: str


class SecuritySettings(FrozenSettingsModel):
    """Safety controls for operations that can change external state."""

    require_apply_flag: bool


class FeatureFlags(FrozenSettingsModel):
    """Runtime feature switches."""

    enable_write_operations: bool


class Settings(BaseSettings):
    """Runtime settings with explicit production safeguards."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = "development"
    log_level: str = "INFO"
    smartsheet_base_url: str = "https://api.smartsheet.com/2.0"
    smartsheet_access_token: str = ""
    smartsheet_tir_sheet_id: str = ""
    database_url: str = "postgresql+psycopg2://user:password@localhost:5432/mise_smartsheet"
    mise_project_root: str = ""
    mise_registry_root: str = ""
    report_export_root: str = DEFAULT_REPORT_FOLDER
    enable_write_operations: bool = False
    require_apply_flag: bool = True

    @property
    def app(self) -> AppSettings:
        """Return grouped application settings."""
        return AppSettings(environment=self.environment, log_level=self.log_level)

    @property
    def smartsheet(self) -> SmartsheetSettings:
        """Return grouped Smartsheet settings."""
        return SmartsheetSettings(
            base_url=self.smartsheet_base_url,
            access_token=self.smartsheet_access_token,
            tir_sheet_id=self.smartsheet_tir_sheet_id,
        )

    @property
    def database(self) -> DatabaseSettings:
        """Return grouped database settings."""
        return DatabaseSettings(url=self.database_url)

    @property
    def filesystem(self) -> FilesystemSettings:
        """Return grouped filesystem settings."""
        return FilesystemSettings(
            mise_project_root=self.mise_project_root,
            mise_registry_root=self.mise_registry_root,
            report_export_root=self.report_export_root,
        )

    @property
    def security(self) -> SecuritySettings:
        """Return grouped security settings."""
        return SecuritySettings(require_apply_flag=self.require_apply_flag)

    @property
    def features(self) -> FeatureFlags:
        """Return grouped feature flag settings."""
        return FeatureFlags(enable_write_operations=self.enable_write_operations)

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        """Require real operational values when production mode is selected."""
        if self.environment != "production":
            return self

        missing_fields = [
            env_name
            for env_name, field_name in REQUIRED_PRODUCTION_FIELDS
            if not getattr(self, field_name)
        ]
        if missing_fields:
            formatted_fields = ", ".join(missing_fields)
            raise ValueError(f"Production settings missing required variables: {formatted_fields}")

        if "user:password@localhost" in self.database_url:
            raise ValueError("Production DATABASE_URL must not use the example local placeholder")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
