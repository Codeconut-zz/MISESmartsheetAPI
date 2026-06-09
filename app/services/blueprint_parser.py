"""Parse architecture blueprints into dry-run plan operations."""

from datetime import UTC, datetime
from pathlib import Path
import hashlib
from typing import Any

from pydantic import ValidationError
import yaml

from app.config import DEFAULT_REPORT_FOLDER
from app.domain.blueprint import ArchitectureBlueprint
from app.domain.plan import OperationRiskLevel, OperationType, Plan, PlanOperation


class BlueprintParseError(ValueError):
    """Raised when an architecture blueprint cannot be parsed safely."""


class BlueprintParser:
    """Load, validate, and convert architecture blueprints."""

    def parse(self, path: str | Path) -> ArchitectureBlueprint:
        """Load and validate an architecture blueprint YAML file."""
        blueprint_path = Path(path)
        if not blueprint_path.exists():
            raise BlueprintParseError(f"Blueprint file not found: {blueprint_path}")

        try:
            raw_data = yaml.safe_load(blueprint_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise BlueprintParseError(f"Blueprint YAML is invalid: {exc}") from exc

        if not isinstance(raw_data, dict):
            raise BlueprintParseError("Blueprint YAML must contain a mapping at the document root")

        try:
            return ArchitectureBlueprint.model_validate(raw_data)
        except ValidationError as exc:
            raise BlueprintParseError(f"Blueprint validation failed: {exc}") from exc

    def to_plan(
        self,
        blueprint: ArchitectureBlueprint,
        *,
        blueprint_path: str | Path,
        report_root: str | Path = DEFAULT_REPORT_FOLDER,
    ) -> Plan:
        """Convert a parsed blueprint into dry-run plan operations."""
        operations = blueprint_plan_operations(blueprint, report_root=report_root)
        return Plan(
            blueprint_path=str(blueprint_path),
            generated_at=datetime.now(UTC),
            operation_count=len(operations),
            operations=operations,
        )


def blueprint_plan_operations(
    blueprint: ArchitectureBlueprint,
    *,
    report_root: str | Path = DEFAULT_REPORT_FOLDER,
) -> list[PlanOperation]:
    """Return dry-run operations implied by architecture blueprint sections."""
    operations: list[PlanOperation] = []
    operations.extend(_report_folder_operations(blueprint, report_root=report_root))
    operations.extend(_department_record_operations(blueprint))
    operations.extend(_division_record_operations(blueprint))
    operations.extend(_standard_sheet_record_operations(blueprint))
    return operations


def _report_folder_operations(
    blueprint: ArchitectureBlueprint,
    *,
    report_root: str | Path,
) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for output_name in blueprint.reporting_outputs:
        target = str(Path(report_root) / output_name)
        operations.append(
            _operation(
                operation_type=OperationType.CREATE_REPORT_FOLDER,
                target=target,
                reason=f"Prepare report output folder for {output_name}",
                before_state={"exists": "unknown"},
                after_state={"exists": True, "folder_name": output_name},
                risk_level=OperationRiskLevel.LOW,
                dry_run_result="Would create report folder if missing",
            )
        )

    return operations


def _department_record_operations(blueprint: ArchitectureBlueprint) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for department in blueprint.departments:
        operations.append(
            _operation(
                operation_type=OperationType.CREATE_DATABASE_RECORD,
                target=f"department_blueprint:{department.code}",
                reason=f"Prepare department blueprint record for {department.name}",
                before_state={"exists": "unknown"},
                after_state={
                    "department_code": department.code,
                    "department_name": department.name,
                    "division_count": len(department.divisions),
                    "director_role_code": department.director_role_code,
                },
                risk_level=OperationRiskLevel.LOW,
                dry_run_result="Would create or refresh department blueprint record",
            )
        )

    return operations


def _division_record_operations(blueprint: ArchitectureBlueprint) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for division in blueprint.all_divisions():
        operations.append(
            _operation(
                operation_type=OperationType.CREATE_DATABASE_RECORD,
                target=f"division_blueprint:{division.department_code}:{division.code}",
                reason=f"Prepare division blueprint record for {division.name}",
                before_state={"exists": "unknown"},
                after_state={
                    "department_code": division.department_code,
                    "division_code": division.code,
                    "division_name": division.name,
                    "head_role": division.head_role,
                },
                risk_level=OperationRiskLevel.LOW,
                dry_run_result="Would create or refresh division blueprint record",
            )
        )

    return operations


def _standard_sheet_record_operations(blueprint: ArchitectureBlueprint) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for sheet in blueprint.standard_sheets:
        operations.append(
            _operation(
                operation_type=OperationType.CREATE_DATABASE_RECORD,
                target=f"standard_sheet_blueprint:{sheet.name}",
                reason=f"Prepare standard sheet blueprint record for {sheet.name}",
                before_state={"exists": "unknown"},
                after_state={"sheet_name": sheet.name, "purpose": sheet.purpose},
                risk_level=OperationRiskLevel.LOW,
                dry_run_result="Would create or refresh standard sheet blueprint record",
            )
        )

    return operations


def _operation(
    *,
    operation_type: OperationType,
    target: str,
    reason: str,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    risk_level: OperationRiskLevel,
    dry_run_result: str,
) -> PlanOperation:
    return PlanOperation(
        operation_id=_operation_id(operation_type, target, reason),
        operation_type=operation_type,
        target=target,
        reason=reason,
        before_state=before_state,
        after_state=after_state,
        risk_level=risk_level,
        dry_run_result=dry_run_result,
    )


def _operation_id(operation_type: OperationType, target: str, reason: str) -> str:
    digest = hashlib.sha256(f"{operation_type}:{target}:{reason}".encode("utf-8")).hexdigest()
    return f"op_{digest[:12]}"
