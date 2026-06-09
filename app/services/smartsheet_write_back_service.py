"""Guarded Smartsheet write-back from approved dry-run plans."""

from datetime import UTC, datetime
from pathlib import Path
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.config import Settings, get_settings
from app.connectors.smartsheet_client import (
    SmartsheetClient,
    SmartsheetSafetyError,
    SmartsheetWriteSafetyContext,
)
from app.domain.plan import OperationType, Plan, PlanOperation
from app.services.audit_service import AuditService, audit_service

ALLOWED_WRITEBACK_FIELDS = {
    "project_folder_path",
    "project_folder_link",
    "reconciliation_status",
    "data_quality_status",
    "integration_last_sync",
}
PROTECTED_WRITEBACK_FIELDS = {"secretary_approval", "contact_email"}
CELL_METADATA_KEYS = {"field", "title", "column_name", "columnName", "name"}


class SmartsheetWriteBackError(ValueError):
    """Raised when a Smartsheet write-back plan cannot be safely applied."""


class SmartsheetWriteBackResult(BaseModel):
    """Summary of Smartsheet rows updated from a plan."""

    model_config = ConfigDict(frozen=True)

    plan_path: str
    updated_count: int
    updated_rows: list[str]
    audit_event_count: int


class SmartsheetWriteBackService:
    """Apply approved UPDATE_SMARTSHEET_ROW operations to Smartsheet."""

    def __init__(
        self,
        *,
        smartsheet_client: SmartsheetClient,
        settings: Settings | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._smartsheet_client = smartsheet_client
        self._settings = settings or get_settings()
        self._audit = audit or audit_service

    def apply_plan(
        self,
        *,
        plan_path: str | Path,
        apply: bool,
        actor: str = "system",
    ) -> SmartsheetWriteBackResult:
        """Apply approved Smartsheet row updates from a plan file."""
        if not self._settings.features.enable_write_operations:
            raise SmartsheetWriteBackError("ENABLE_WRITE_OPERATIONS=true is required")
        if self._settings.security.require_apply_flag and not apply:
            raise SmartsheetWriteBackError("Explicit --apply is required")

        input_path = Path(plan_path)
        if not input_path.exists():
            raise SmartsheetWriteBackError(f"Plan file not found: {input_path}")

        plan = load_plan(input_path)
        operations = [
            operation
            for operation in plan.operations
            if operation.operation_type == OperationType.UPDATE_SMARTSHEET_ROW
        ]
        approved_operation_ids = frozenset(operation.operation_id for operation in plan.operations)
        initial_audit_count = len(self._audit.list_events())
        updated_rows: list[str] = []

        for operation in operations:
            sheet_id, row_id = _row_identity(operation)
            cells = _writeback_cells(operation)
            safety_context = SmartsheetWriteSafetyContext(
                dry_run_completed=True,
                enable_write_operations=self._settings.features.enable_write_operations,
                apply_requested=apply,
                operation_id=operation.operation_id,
                approved_operation_ids=approved_operation_ids,
                plan_path=str(input_path),
            )
            target_id = f"{sheet_id}:{row_id}"
            self._audit.record(
                actor=actor,
                action="update_smartsheet_row",
                target_type="smartsheet_row",
                target_id=target_id,
                status="pending",
                dry_run=False,
                message="Updating Smartsheet row from approved plan",
                metadata={"operation_id": operation.operation_id, "plan_path": str(input_path)},
            )
            try:
                self._smartsheet_client.update_row_cells(
                    sheet_id,
                    row_id,
                    cells,
                    safety_context=safety_context,
                )
            except SmartsheetSafetyError as exc:
                raise SmartsheetWriteBackError(str(exc)) from exc

            updated_rows.append(target_id)
            self._audit.record(
                actor=actor,
                action="update_smartsheet_row",
                target_type="smartsheet_row",
                target_id=target_id,
                status="success",
                dry_run=False,
                message="Updated Smartsheet row from approved plan",
                metadata={"operation_id": operation.operation_id, "plan_path": str(input_path)},
            )

        return SmartsheetWriteBackResult(
            plan_path=str(input_path),
            updated_count=len(updated_rows),
            updated_rows=updated_rows,
            audit_event_count=len(self._audit.list_events()) - initial_audit_count,
        )


def load_plan(path: str | Path) -> Plan:
    """Load a dry-run plan from JSON."""
    input_path = Path(path)
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SmartsheetWriteBackError(f"Plan JSON is invalid: {exc}") from exc

    return Plan.model_validate(payload)


def _row_identity(operation: PlanOperation) -> tuple[str, str]:
    sheet_id = _operation_state_value(operation, "sheet_id")
    row_id = _operation_state_value(operation, "row_id")
    if not sheet_id or not row_id:
        parsed_sheet_id, parsed_row_id = _parse_target_identity(operation.target)
        sheet_id = sheet_id or parsed_sheet_id
        row_id = row_id or parsed_row_id
    if not sheet_id or not row_id:
        raise SmartsheetWriteBackError(
            f"Operation {operation.operation_id} must include sheet_id and row_id"
        )

    return sheet_id, row_id


def _operation_state_value(operation: PlanOperation, key: str) -> str:
    for state in (operation.after_state, operation.before_state):
        value = state.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def _parse_target_identity(target: str) -> tuple[str, str]:
    values: dict[str, str] = {}
    for part in target.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        values[_normalize_field_name(key)] = value.strip()

    return values.get("sheet_id", ""), values.get("row_id", "")


def _writeback_cells(operation: PlanOperation) -> list[dict[str, Any]]:
    raw_cells = operation.after_state.get("cells", [])
    if not isinstance(raw_cells, list) or not raw_cells:
        raise SmartsheetWriteBackError(
            f"Operation {operation.operation_id} must include after_state.cells"
        )

    cells: list[dict[str, Any]] = []
    for raw_cell in raw_cells:
        if not isinstance(raw_cell, dict):
            raise SmartsheetWriteBackError("Write-back cells must be objects")
        cells.append(_safe_cell(raw_cell))

    return cells


def _safe_cell(raw_cell: dict[str, Any]) -> dict[str, Any]:
    field_name = _cell_field_name(raw_cell)
    if not field_name:
        raise SmartsheetWriteBackError("Write-back cells must include field metadata")

    normalized_field = _normalize_field_name(field_name)
    if normalized_field in PROTECTED_WRITEBACK_FIELDS:
        raise SmartsheetWriteBackError(f"Protected Smartsheet field cannot be updated: {field_name}")
    if normalized_field not in ALLOWED_WRITEBACK_FIELDS:
        raise SmartsheetWriteBackError(f"Smartsheet field is not allowed for write-back: {field_name}")
    if "columnId" not in raw_cell:
        raise SmartsheetWriteBackError(f"Write-back cell for {field_name} must include columnId")

    cell = {key: value for key, value in raw_cell.items() if key not in CELL_METADATA_KEYS}
    if normalized_field == "integration_last_sync" and "value" not in cell:
        cell["value"] = datetime.now(UTC).isoformat()

    return cell


def _cell_field_name(raw_cell: dict[str, Any]) -> str:
    for key in CELL_METADATA_KEYS:
        value = raw_cell.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def _normalize_field_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
