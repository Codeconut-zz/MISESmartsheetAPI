"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]

REQUIRED_PRODUCTION_FIELDS = (
    "smartsheet_access_token",
    "smartsheet_tir_sheet_id",
    "database_url",
    "mise_project_root",
    "mise_registry_root",
)


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
    report_export_root: str = "data/reports"
    enable_write_operations: bool = False
    require_apply_flag: bool = True

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        """Require real operational values when production mode is selected."""
        if self.environment != "production":
            return self

        missing_fields = [
            field_name for field_name in REQUIRED_PRODUCTION_FIELDS if not getattr(self, field_name)
        ]
        if missing_fields:
            formatted_fields = ", ".join(missing_fields)
            raise ValueError(f"Production settings missing required values: {formatted_fields}")

        if "user:password@localhost" in self.database_url:
            raise ValueError("Production DATABASE_URL must not use the example local placeholder")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
