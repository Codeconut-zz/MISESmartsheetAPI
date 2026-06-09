"""Dry-run planner for proposed write operations."""

from pathlib import Path
import hashlib
import json
import re
from typing import Any

from app.config import DEFAULT_REPORT_FOLDER
from app.domain.blueprint import ArchitectureBlueprint
from app.domain.plan import OperationRiskLevel, OperationType, Plan, PlanOperation
from app.domain.tir import TechnicalIntakeRequest
from app.services.blueprint_parser import BlueprintParser, blueprint_plan_operations
from app.services.reconciliation_service import (
    ReconciliationResult,
    ReconciliationService,
    load_folder_inventory_export,
    load_tir_records_export,
)
from app.services.report_export_service import load_reconciliation_results


class DryRunPlanner:
    """Build previews for write operations without executing them."""

    def build_plan(
        self,
        *,
        blueprint_path: str | Path,
        report_root: str | Path = DEFAULT_REPORT_FOLDER,
        tir_path: str | Path | None = None,
        folders_path: str | Path | None = None,
        reconciliation_path: str | Path | None = None,
    ) -> Plan:
        """Return a dry-run plan from blueprint and optional workflow exports."""
        blueprint = BlueprintParser().parse(blueprint_path)
        operations = blueprint_plan_operations(blueprint, report_root=report_root)
        warnings: list[str] = []

        tir_records: list[TechnicalIntakeRequest] = []
        reconciliation_results: list[ReconciliationResult] = []
        if tir_path is not None:
            tir_records = load_tir_records_export(tir_path)
        if reconciliation_path is not None:
            reconciliation_results = load_reconciliation_results(reconciliation_path)
        elif tir_path is not None and folders_path is not None:
            reconciliation_results = ReconciliationService().reconcile(
                tir_records=tir_records,
                folder_inventory=load_folder_inventory_export(folders_path),
            )
        elif tir_path is not None or folders_path is not None:
            warnings.append("TIR and folder exports are both required to plan reconciliation actions")

        if tir_records and reconciliation_results:
            operations.extend(_reconciliation_operations(blueprint, tir_records, reconciliation_results))

        return Plan(
            blueprint_path=str(blueprint_path),
            operation_count=len(operations),
            operations=operations,
            warnings=warnings,
        )


def export_plan(plan: Plan, out: str | Path, *, pretty: bool = True) -> None:
    """Write a dry-run plan JSON document."""
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(plan.model_dump(mode="json"), indent=indent, sort_keys=pretty),
        encoding="utf-8",
    )

def _reconciliation_operations(
    blueprint: ArchitectureBlueprint,
    tir_records: list[TechnicalIntakeRequest],
    reconciliation_results: list[ReconciliationResult],
) -> list[PlanOperation]:
    tir_by_ref = {tir.registry_file_ref: tir for tir in tir_records if tir.registry_file_ref}
    operations: list[PlanOperation] = []
    for result in reconciliation_results:
        tir = tir_by_ref.get(result.registry_file_ref)
        if result.category == "MISSING_FOLDER" and tir is not None:
            operations.append(_create_project_folder_operation(blueprint, tir))
        if result.category in {"MATCHED", "POSSIBLE_MATCH"}:
            operations.append(_smartsheet_status_update_operation(result))
        if result.matched_folder_path:
            operations.append(_attachment_link_operation(result))

    return operations


def _create_project_folder_operation(
    blueprint: ArchitectureBlueprint,
    tir: TechnicalIntakeRequest,
) -> PlanOperation:
    target = _project_folder_target(blueprint, tir)
    return _operation(
        operation_type=OperationType.CREATE_PROJECT_FOLDER,
        target=target,
        reason="Reconciliation found no existing project folder for this TIR record",
        before_state={"exists": False, "registry_file_ref": tir.registry_file_ref},
        after_state={
            "exists": True,
            "folder_name": Path(target).name,
            "standard_subfolders": list(blueprint.standard_folders),
        },
        risk_level=OperationRiskLevel.MEDIUM,
        dry_run_result="Would create project folder and standard subfolders",
    )


def _smartsheet_status_update_operation(result: ReconciliationResult) -> PlanOperation:
    return _operation(
        operation_type=OperationType.UPDATE_SMARTSHEET_ROW,
        target=f"tir_registry_file_ref:{result.registry_file_ref}",
        reason="Publish reconciliation status back to the TIR row",
        before_state={"reconciliation_status": "unknown"},
        after_state={
            "reconciliation_status": result.category,
            "confidence_score": result.confidence_score,
            "matched_folder_path": result.matched_folder_path,
        },
        risk_level=OperationRiskLevel.HIGH,
        dry_run_result="Would update allowed Smartsheet write-back columns",
    )


def _attachment_link_operation(result: ReconciliationResult) -> PlanOperation:
    return _operation(
        operation_type=OperationType.ADD_SMARTSHEET_ATTACHMENT_LINK,
        target=f"tir_registry_file_ref:{result.registry_file_ref}",
        reason="Attach matched project folder link to the TIR row",
        before_state={"attachment_link": "unknown"},
        after_state={"attachment_link": result.matched_folder_path},
        risk_level=OperationRiskLevel.HIGH,
        dry_run_result="Would add Smartsheet attachment link to matched folder",
    )


def _project_folder_target(blueprint: ArchitectureBlueprint, tir: TechnicalIntakeRequest) -> str:
    pattern = blueprint.folder_rules.project_folder_pattern
    folder_name = pattern.format(
        registry_file_ref=tir.registry_file_ref,
        project_name=tir.project_name,
        department_code=tir.mise_hod,
    )
    if blueprint.folder_rules.sanitize_invalid_path_characters:
        folder_name = _sanitize_path_component(folder_name)

    return str(Path(tir.mise_hod) / folder_name)


def _sanitize_path_component(value: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    return sanitized or "untitled-project"


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
