"""Guarded project folder creation from dry-run plans."""

from pathlib import Path
import json
import re

from pydantic import BaseModel, ConfigDict

from app.config import Settings, get_settings
from app.domain.plan import OperationType, Plan, PlanOperation
from app.services.audit_service import AuditService, audit_service


class ProjectFolderCreationError(ValueError):
    """Raised when a folder plan cannot be safely applied."""


class ProjectFolderCreationResult(BaseModel):
    """Summary of folders created from a plan."""

    model_config = ConfigDict(frozen=True)

    plan_path: str
    created_count: int
    created_folders: list[str]
    audit_event_count: int


class ProjectFolderCreationService:
    """Create project folders only through explicit, audited apply operations."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._audit = audit or audit_service

    def apply_plan(
        self,
        *,
        plan_path: str | Path,
        apply: bool,
        project_root: str | Path | None = None,
        actor: str = "system",
    ) -> ProjectFolderCreationResult:
        """Apply CREATE_PROJECT_FOLDER operations from an existing plan file."""
        if not self._settings.features.enable_write_operations:
            raise ProjectFolderCreationError("ENABLE_WRITE_OPERATIONS=true is required")
        if self._settings.security.require_apply_flag and not apply:
            raise ProjectFolderCreationError("Explicit --apply is required")

        input_path = Path(plan_path)
        if not input_path.exists():
            raise ProjectFolderCreationError(f"Plan file not found: {input_path}")

        root = _resolve_project_root(project_root, self._settings)
        plan = load_plan(input_path)
        operations = [
            operation
            for operation in plan.operations
            if operation.operation_type == OperationType.CREATE_PROJECT_FOLDER
        ]
        targets = [_safe_target_path(root, operation) for operation in operations]
        _validate_unique_targets(targets)
        _validate_targets_do_not_exist(targets)

        created_folders: list[str] = []
        initial_audit_count = len(self._audit.list_events())
        for operation, target in zip(operations, targets, strict=True):
            self._audit.record(
                actor=actor,
                action="create_project_folder",
                target_type="folder",
                target_id=str(target),
                status="pending",
                dry_run=False,
                message="Creating project folder from approved plan",
                metadata={"operation_id": operation.operation_id, "plan_path": str(input_path)},
            )
            _create_project_folder(target, operation)
            created_folders.append(str(target))
            self._audit.record(
                actor=actor,
                action="create_project_folder",
                target_type="folder",
                target_id=str(target),
                status="success",
                dry_run=False,
                message="Created project folder from approved plan",
                metadata={"operation_id": operation.operation_id, "plan_path": str(input_path)},
            )

        return ProjectFolderCreationResult(
            plan_path=str(input_path),
            created_count=len(created_folders),
            created_folders=created_folders,
            audit_event_count=len(self._audit.list_events()) - initial_audit_count,
        )


def load_plan(path: str | Path) -> Plan:
    """Load a dry-run plan from JSON."""
    input_path = Path(path)
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectFolderCreationError(f"Plan JSON is invalid: {exc}") from exc

    return Plan.model_validate(payload)


def _resolve_project_root(project_root: str | Path | None, settings: Settings) -> Path:
    configured_root = project_root or settings.filesystem.mise_project_root
    if not configured_root:
        raise ProjectFolderCreationError("MISE_PROJECT_ROOT is required for folder creation")

    root = Path(configured_root).expanduser()
    if not root.exists():
        raise ProjectFolderCreationError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise ProjectFolderCreationError(f"Project root is not a directory: {root}")

    return root.resolve()


def _safe_target_path(root: Path, operation: PlanOperation) -> Path:
    target = Path(operation.target)
    if target.is_absolute():
        raise ProjectFolderCreationError(f"Project folder target must be relative: {operation.target}")
    if any(part == ".." for part in target.parts):
        raise ProjectFolderCreationError(f"Project folder target must not contain '..': {operation.target}")

    sanitized_parts = [_sanitize_path_component(part) for part in target.parts if part not in {"", "."}]
    if not sanitized_parts:
        raise ProjectFolderCreationError("Project folder target is empty after sanitization")

    resolved_target = (root / Path(*sanitized_parts)).resolve()
    if not _is_within_root(resolved_target, root):
        raise ProjectFolderCreationError(f"Project folder target escapes project root: {operation.target}")

    return resolved_target


def _validate_unique_targets(targets: list[Path]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for target in targets:
        key = str(target).casefold()
        if key in seen:
            duplicates.append(str(target))
        seen.add(key)

    if duplicates:
        formatted = ", ".join(sorted(set(duplicates)))
        raise ProjectFolderCreationError(f"Duplicate target folders in plan: {formatted}")


def _validate_targets_do_not_exist(targets: list[Path]) -> None:
    existing = [str(target) for target in targets if target.exists()]
    if existing:
        formatted = ", ".join(sorted(existing))
        raise ProjectFolderCreationError(f"Target folder already exists; refusing to overwrite: {formatted}")


def _create_project_folder(target: Path, operation: PlanOperation) -> None:
    target.mkdir(parents=True, exist_ok=False)
    for folder_name in _standard_subfolders(operation):
        (target / _sanitize_path_component(folder_name)).mkdir(exist_ok=False)


def _standard_subfolders(operation: PlanOperation) -> list[str]:
    subfolders = operation.after_state.get("standard_subfolders", [])
    if not isinstance(subfolders, list):
        return []

    return [str(folder_name) for folder_name in subfolders if str(folder_name).strip()]


def _sanitize_path_component(value: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    return sanitized or "untitled-project"


def _is_within_root(target: Path, root: Path) -> bool:
    try:
        target.relative_to(root)
    except ValueError:
        return False

    return True
