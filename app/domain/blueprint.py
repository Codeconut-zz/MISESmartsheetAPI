"""Architecture blueprint domain models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.plan import OperationType


class BlueprintModel(BaseModel):
    """Base model for validated blueprint objects."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class BlueprintMinistry(BlueprintModel):
    """Ministry metadata from the architecture blueprint."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    reporting_timezone: str = Field(min_length=1)


class BlueprintDivision(BlueprintModel):
    """Division metadata from either a department or top-level section."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    head_role: str = Field(min_length=1)
    department_code: str = ""

    @field_validator("code", "name", "head_role", "department_code", mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> str:
        """Strip text fields."""
        return "" if value is None else str(value).strip()


class BlueprintDepartment(BlueprintModel):
    """Department metadata from the architecture blueprint."""

    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    director_role_code: str = ""
    divisions: list[BlueprintDivision] = Field(default_factory=list)

    @field_validator("code", "name", "director_role_code", mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> str:
        """Strip text fields."""
        return "" if value is None else str(value).strip()


class StandardSheet(BlueprintModel):
    """Standard Smartsheet definition requested by the blueprint."""

    name: str = Field(min_length=1)
    purpose: str = ""

    @field_validator("name", "purpose", mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> str:
        """Strip text fields."""
        return "" if value is None else str(value).strip()


class FolderRules(BlueprintModel):
    """Safety rules for project folder operations."""

    project_folder_pattern: str = "{registry_file_ref} - {project_name}"
    sanitize_invalid_path_characters: bool = True
    no_overwrite: bool = True
    allowed_operation_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_folder_rules(self) -> "FolderRules":
        """Reject unsafe or unknown folder operation rules."""
        required_tokens = {"{registry_file_ref}", "{project_name}"}
        missing_tokens = [
            token for token in required_tokens if token not in self.project_folder_pattern
        ]
        if missing_tokens:
            formatted = ", ".join(missing_tokens)
            raise ValueError(f"project_folder_pattern missing required token(s): {formatted}")
        if not self.no_overwrite:
            raise ValueError("folder_rules.no_overwrite must be true")

        allowed_operation_values = {operation.value for operation in OperationType}
        unknown_operations = [
            operation
            for operation in self.allowed_operation_types
            if operation not in allowed_operation_values
        ]
        if unknown_operations:
            formatted = ", ".join(sorted(unknown_operations))
            raise ValueError(f"Unknown or risky operation type(s): {formatted}")

        return self


class SmartsheetWritebackRules(BlueprintModel):
    """Write-back allow/protect list from the architecture blueprint."""

    protected_columns: list[str] = Field(default_factory=list)
    allowed_columns: list[str] = Field(default_factory=list)


class ArchitectureBlueprint(BlueprintModel):
    """Validated ministry architecture blueprint."""

    ministry: BlueprintMinistry
    departments: list[BlueprintDepartment] = Field(default_factory=list)
    divisions: list[BlueprintDivision] = Field(default_factory=list)
    standard_folders: list[str] = Field(default_factory=list)
    standard_sheets: list[StandardSheet] = Field(default_factory=list)
    reporting_outputs: list[str] = Field(default_factory=list)
    folder_rules: FolderRules = Field(default_factory=FolderRules)
    smartsheet_writeback_rules: SmartsheetWritebackRules = Field(
        default_factory=SmartsheetWritebackRules
    )
    roles: list[dict[str, Any]] = Field(default_factory=list)
    reporting_lines: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("standard_folders", "reporting_outputs", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        """Normalize simple string-list sections."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Blueprint section must be a list")

        return [str(item).strip() for item in value if str(item).strip()]

    @field_validator("standard_sheets", mode="before")
    @classmethod
    def normalize_standard_sheets(cls, value: Any) -> list[Any]:
        """Allow standard_sheets as strings or mappings."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("standard_sheets must be a list")

        return [
            {"name": item}
            if isinstance(item, str)
            else item
            for item in value
        ]

    @model_validator(mode="after")
    def validate_blueprint(self) -> "ArchitectureBlueprint":
        """Validate uniqueness and top-level division references."""
        duplicate_department_codes = _duplicates(department.code for department in self.departments)
        if duplicate_department_codes:
            formatted = ", ".join(sorted(duplicate_department_codes))
            raise ValueError(f"Duplicate department code(s): {formatted}")

        department_codes = {department.code for department in self.departments}
        for division in self.divisions:
            if division.department_code not in department_codes:
                raise ValueError(
                    f"Division {division.code} references unknown department {division.department_code}"
                )

        for department in self.departments:
            duplicate_division_codes = _duplicates(division.code for division in department.divisions)
            if duplicate_division_codes:
                formatted = ", ".join(sorted(duplicate_division_codes))
                raise ValueError(
                    f"Duplicate division code(s) in department {department.code}: {formatted}"
                )

        return self

    def all_divisions(self) -> list[BlueprintDivision]:
        """Return nested and top-level divisions."""
        divisions = list(self.divisions)
        for department in self.departments:
            divisions.extend(
                division.model_copy(update={"department_code": division.department_code or department.code})
                for division in department.divisions
            )

        return divisions


def _duplicates(values: Any) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return duplicates
