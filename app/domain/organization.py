"""MISE organization domain models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrganizationModel(BaseModel):
    """Base model for immutable organization objects."""

    model_config = ConfigDict(frozen=True)


class Role(OrganizationModel):
    """A role in the MISE reporting hierarchy."""

    code: str = Field(min_length=1)
    title: str = Field(min_length=1)

    @field_validator("code", "title", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        """Strip and validate required text fields."""
        return str(value).strip()


class Division(OrganizationModel):
    """A department division."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    head_role: str = Field(min_length=1)

    @field_validator("code", "name", "head_role", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        """Strip and validate required text fields."""
        return str(value).strip()


class Department(OrganizationModel):
    """A MISE department."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    director_role_code: str = Field(min_length=1)
    divisions: list[Division] = Field(default_factory=list)

    @field_validator("code", "name", "director_role_code", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        """Strip and validate required text fields."""
        return str(value).strip()


class ReportingLine(OrganizationModel):
    """A reporting relationship between two roles."""

    supervisor_role_code: str = Field(min_length=1)
    report_role_code: str = Field(min_length=1)

    @field_validator("supervisor_role_code", "report_role_code", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        """Strip and validate required text fields."""
        return str(value).strip()


class Ministry(OrganizationModel):
    """Ministry-level metadata."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    reporting_timezone: str = Field(min_length=1)


class OrganizationBlueprint(OrganizationModel):
    """Validated MISE ministry blueprint."""

    ministry: Ministry
    roles: list[Role] = Field(default_factory=list)
    reporting_lines: list[ReportingLine] = Field(default_factory=list)
    standard_folders: list[str] = Field(default_factory=list)
    departments: list[Department] = Field(default_factory=list)
    folder_rules: dict[str, Any] = Field(default_factory=dict)
    reporting_outputs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "OrganizationBlueprint":
        """Ensure reporting and department role references point to known roles."""
        role_codes = {role.code for role in self.roles}
        missing_role_codes = set()

        for line in self.reporting_lines:
            if line.supervisor_role_code not in role_codes:
                missing_role_codes.add(line.supervisor_role_code)
            if line.report_role_code not in role_codes:
                missing_role_codes.add(line.report_role_code)

        for department in self.departments:
            if department.director_role_code not in role_codes:
                missing_role_codes.add(department.director_role_code)

        if missing_role_codes:
            formatted_codes = ", ".join(sorted(missing_role_codes))
            raise ValueError(f"Blueprint references undefined role codes: {formatted_codes}")

        return self

    def department_by_code(self, code: str) -> Department:
        """Return a department by code."""
        for department in self.departments:
            if department.code == code:
                return department

        raise KeyError(code)
