import json
from pathlib import Path

from typer.testing import CliRunner

from app.cli.main import app
from app.config import Settings, get_settings
from app.domain.plan import OperationRiskLevel, OperationType, Plan, PlanOperation
from app.services.audit_service import AuditService, InMemoryAuditSink
from app.services.dry_run_planner import export_plan
from app.services.project_folder_creation_service import (
    ProjectFolderCreationError,
    ProjectFolderCreationService,
)

runner = CliRunner()


def make_plan(*operations: PlanOperation) -> Plan:
    return Plan(
        blueprint_path="config/architecture/mise_ministry_blueprint.example.yaml",
        operation_count=len(operations),
        operations=list(operations),
    )


def make_folder_operation(
    *,
    operation_id: str = "op-folder-1",
    target: str = "ABED/MISE:ABED?001 - Community <hall>",
) -> PlanOperation:
    return PlanOperation(
        operation_id=operation_id,
        operation_type=OperationType.CREATE_PROJECT_FOLDER,
        target=target,
        reason="Create missing project folder",
        before_state={"exists": False, "registry_file_ref": "MISE-ABED-001"},
        after_state={
            "exists": True,
            "folder_name": "MISE-ABED-001 - Community hall",
            "standard_subfolders": ["01 - Intake", "02 - Active Projects"],
        },
        risk_level=OperationRiskLevel.MEDIUM,
        dry_run_result="Would create project folder and standard subfolders",
    )


def write_plan(tmp_path: Path, plan: Plan) -> Path:
    plan_path = tmp_path / "plan.json"
    export_plan(plan, plan_path)
    return plan_path


def enabled_settings(root: Path) -> Settings:
    return Settings(
        environment="test",
        enable_write_operations=True,
        mise_project_root=str(root),
        _env_file=None,
    )


def test_folder_creation_requires_write_flag(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_folder_operation()))
    service = ProjectFolderCreationService(
        settings=Settings(environment="test", enable_write_operations=False, _env_file=None)
    )

    try:
        service.apply_plan(plan_path=plan_path, apply=True, project_root=tmp_path)
    except ProjectFolderCreationError as exc:
        assert "ENABLE_WRITE_OPERATIONS" in str(exc)
    else:
        raise AssertionError("folder creation should require ENABLE_WRITE_OPERATIONS=true")


def test_folder_creation_requires_apply_flag(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_folder_operation()))
    service = ProjectFolderCreationService(settings=enabled_settings(tmp_path))

    try:
        service.apply_plan(plan_path=plan_path, apply=False)
    except ProjectFolderCreationError as exc:
        assert "--apply" in str(exc)
    else:
        raise AssertionError("folder creation should require explicit --apply")


def test_folder_creation_creates_sanitized_folder_and_audit_events(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_folder_operation()))
    sink = InMemoryAuditSink()
    service = ProjectFolderCreationService(
        settings=enabled_settings(tmp_path),
        audit=AuditService(sink=sink),
    )

    result = service.apply_plan(plan_path=plan_path, apply=True, actor="tester")

    target = tmp_path / "ABED" / "MISE-ABED-001 - Community -hall-"
    assert result.created_count == 1
    assert target.exists()
    assert (target / "01 - Intake").exists()
    assert (target / "02 - Active Projects").exists()
    assert result.audit_event_count == 2
    assert [event.status for event in sink.list_events()] == ["pending", "success"]


def test_folder_creation_refuses_existing_folder(tmp_path: Path) -> None:
    target = tmp_path / "ABED" / "MISE-ABED-001 - Community -hall-"
    target.mkdir(parents=True)
    plan_path = write_plan(tmp_path, make_plan(make_folder_operation()))
    service = ProjectFolderCreationService(settings=enabled_settings(tmp_path))

    try:
        service.apply_plan(plan_path=plan_path, apply=True)
    except ProjectFolderCreationError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("folder creation should refuse existing folders")


def test_folder_creation_rejects_duplicate_targets(tmp_path: Path) -> None:
    plan_path = write_plan(
        tmp_path,
        make_plan(
            make_folder_operation(operation_id="op-folder-1"),
            make_folder_operation(operation_id="op-folder-2"),
        ),
    )
    service = ProjectFolderCreationService(settings=enabled_settings(tmp_path))

    try:
        service.apply_plan(plan_path=plan_path, apply=True)
    except ProjectFolderCreationError as exc:
        assert "Duplicate target folders" in str(exc)
    else:
        raise AssertionError("folder creation should reject duplicate targets")

    assert not (tmp_path / "ABED" / "MISE-ABED-001 - Community -hall-").exists()


def test_apply_folder_plan_cli_uses_plan_file_and_apply_flag(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_folder_operation()))
    monkeypatch.setenv("ENABLE_WRITE_OPERATIONS", "true")
    monkeypatch.setenv("MISE_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = runner.invoke(app, ["apply-folder-plan", str(plan_path), "--apply"])

    get_settings.cache_clear()
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["created_count"] == 1
    assert (tmp_path / "ABED" / "MISE-ABED-001 - Community -hall-").exists()
