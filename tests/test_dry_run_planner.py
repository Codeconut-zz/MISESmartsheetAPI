import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from app.cli import main as cli
from app.cli.main import app
from app.domain.plan import OperationType
from app.services.dry_run_planner import DryRunPlanner, export_plan
from tests.test_reconciliation_service import make_folder, make_tir

BLUEPRINT_PATH = Path("config/architecture/mise_ministry_blueprint.example.yaml")
runner = CliRunner()


def test_dry_run_plan_includes_blueprint_operations() -> None:
    plan = DryRunPlanner().build_plan(blueprint_path=BLUEPRINT_PATH)

    operation_types = {operation.operation_type for operation in plan.operations}

    assert plan.operation_count == len(plan.operations)
    assert OperationType.CREATE_REPORT_FOLDER in operation_types
    assert OperationType.CREATE_DATABASE_RECORD in operation_types
    assert all(operation.dry_run_result.startswith("Would") for operation in plan.operations)


def test_dry_run_plan_adds_reconciliation_actions(tmp_path: Path) -> None:
    tir = make_tir(registry_file_ref="MISE-WSED-009", project_name="Water pump replacement")
    folder = make_folder(registry_file_ref="MISE-ABED-001", project_name="Community hall roof repair")
    tir_path = tmp_path / "tir.json"
    folders_path = tmp_path / "folders.json"
    tir_path.write_text(json.dumps({"normalized": [tir.model_dump(mode="json")]}), encoding="utf-8")
    folders_path.write_text(
        json.dumps({"inventory": [folder.model_dump(mode="json")]}),
        encoding="utf-8",
    )

    plan = DryRunPlanner().build_plan(
        blueprint_path=BLUEPRINT_PATH,
        tir_path=tir_path,
        folders_path=folders_path,
    )

    folder_operations = [
        operation
        for operation in plan.operations
        if operation.operation_type == OperationType.CREATE_PROJECT_FOLDER
    ]
    assert len(folder_operations) == 1
    assert "MISE-WSED-009 - Water pump replacement" in folder_operations[0].target
    assert folder_operations[0].before_state["exists"] is False


def test_plan_export_writes_json(tmp_path: Path) -> None:
    plan = DryRunPlanner().build_plan(blueprint_path=BLUEPRINT_PATH)
    output_path = tmp_path / "plan.json"

    export_plan(plan, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["operation_count"] == len(payload["operations"])
    assert payload["operations"][0]["operation_id"].startswith("op_")


def test_plan_cli_outputs_json_without_smartsheet_writes(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    def fail_if_smartsheet_requested() -> None:
        raise AssertionError("planning must not initialize Smartsheet write connectors")

    monkeypatch.setattr(cli, "get_smartsheet_client", fail_if_smartsheet_requested)
    output_path = tmp_path / "plan.json"

    result = runner.invoke(
        app,
        [
            "plan",
            str(BLUEPRINT_PATH),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "planned"
    assert payload["operation_count"] > 0
    assert output_path.exists()
