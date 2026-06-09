"""Technical Intake Request domain model."""

from datetime import datetime
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ProjectStatus = Literal[
    "NEW",
    "PENDING",
    "APPROVED",
    "DECLINED",
    "IN_PROGRESS",
    "COMPLETED",
    "ARCHIVED",
]

PROJECT_STATUSES = {
    "NEW",
    "PENDING",
    "APPROVED",
    "DECLINED",
    "IN_PROGRESS",
    "COMPLETED",
    "ARCHIVED",
}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TechnicalIntakeRequest(BaseModel):
    """Normalized Technical Intake Request row."""

    model_config = ConfigDict(frozen=True)

    created: datetime
    secretary_approval: bool
    mise_hod: str = Field(min_length=1)
    registry_confirmation: bool
    registry_file_ref: str = ""
    client_file_ref: str = ""
    organisation: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    service_request: str = Field(min_length=1)
    project_location: str = Field(min_length=1)
    project_status: ProjectStatus
    contact_person: str = Field(min_length=1)
    contact_person_position: str = ""
    contact_number: str = ""
    contact_email: str = Field(min_length=1)
    project_background_information: str = ""
    funding_source: str = ""

    @field_validator(
        "mise_hod",
        "registry_file_ref",
        "client_file_ref",
        "organisation",
        "project_name",
        "service_request",
        "project_location",
        "contact_person",
        "contact_person_position",
        "contact_number",
        "contact_email",
        "project_background_information",
        "funding_source",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Any) -> str:
        """Normalize string-like fields while preserving multiline text."""
        if value is None:
            return ""

        return str(value).strip()

    @field_validator("secretary_approval", "registry_confirmation", mode="before")
    @classmethod
    def normalize_boolean(cls, value: Any) -> bool:
        """Normalize Smartsheet boolean-ish values."""
        if isinstance(value, bool):
            return value
        if value is None or value == "":
            return False
        if isinstance(value, int):
            raise ValueError("Boolean fields must not be provided as integers")

        normalized = str(value).strip().lower()
        if normalized in {"true", "yes", "y", "approved", "confirmed"}:
            return True
        if normalized in {"false", "no", "n", "declined", "pending", "unconfirmed"}:
            return False

        raise ValueError(f"Unrecognized boolean value: {value}")

    @field_validator("project_status", mode="before")
    @classmethod
    def normalize_project_status(cls, value: Any) -> str:
        """Normalize and validate TIR project status values."""
        normalized = str(value).strip().upper().replace("-", "_").replace(" ", "_")
        if normalized not in PROJECT_STATUSES:
            raise ValueError(f"Unknown project status: {value}")

        return normalized

    @field_validator("contact_number", mode="before")
    @classmethod
    def require_phone_as_string(cls, value: Any) -> Any:
        """Reject numeric phone values to preserve leading zeros and symbols."""
        if isinstance(value, int):
            raise ValueError("CONTACT NUMBER must be a string, not an integer")

        return value

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate contact email format without requiring extra dependencies."""
        if not EMAIL_PATTERN.match(value):
            raise ValueError("CONTACT EMAIL must be a valid email address")

        return value
