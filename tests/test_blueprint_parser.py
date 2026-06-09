from pathlib import Path

import pytest

from app.domain.plan import OperationType
from app.services.blueprint_parser import BlueprintParseError, BlueprintParser
from app.services.dry_run_planner import DryRunPlanner

BLUEPRINT_PATH = Path("config/architecture/mise_ministry_blueprint.example.yaml")


def test_blueprint_parser_loads_valid_blueprint() -> None:
    blueprint = BlueprintParser().parse(BLUEPRINT_PATH)

    assert blueprint.ministry.code == "MISE"
    assert len(blueprint.departments) == 5
    assert [sheet.name for sheet in blueprint.standard_sheets] == [
        "TIR Register",
        "Project Folder Register",
        "Data Quality Register",
    ]
    assert "CONTACT EMAIL" in blueprint.smartsheet_writeback_rules.protected_columns


def test_blueprint_parser_rejects_missing_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "missing_ministry.yaml"
    path.write_text("departments: []\n", encoding="utf-8")

    with pytest.raises(BlueprintParseError, match="Blueprint validation failed"):
        BlueprintParser().parse(path)


def test_blueprint_parser_rejects_duplicate_department_codes(tmp_path: Path) -> None:
    path = tmp_path / "duplicate_departments.yaml"
    path.write_text(
        """
ministry:
  code: MISE
  name: Ministry
  reporting_timezone: Pacific/Tarawa
departments:
  - code: ABED
    name: Architectural Building
  - code: ABED
    name: Duplicate Architectural Building
folder_rules:
  project_folder_pattern: "{registry_file_ref} - {project_name}"
  no_overwrite: true
""",
        encoding="utf-8",
    )

    with pytest.raises(BlueprintParseError, match="Duplicate department code"):
        BlueprintParser().parse(path)


def test_blueprint_parser_rejects_invalid_folder_rules(tmp_path: Path) -> None:
    path = tmp_path / "invalid_folder_rules.yaml"
    path.write_text(
        """
ministry:
  code: MISE
  name: Ministry
  reporting_timezone: Pacific/Tarawa
departments:
  - code: ABED
    name: Architectural Building
folder_rules:
  project_folder_pattern: "{project_name}"
  no_overwrite: false
""",
        encoding="utf-8",
    )

    with pytest.raises(BlueprintParseError, match="project_folder_pattern|no_overwrite"):
        BlueprintParser().parse(path)


def test_blueprint_parser_rejects_unknown_risky_operation_types(tmp_path: Path) -> None:
    path = tmp_path / "risky_operation.yaml"
    path.write_text(
        """
ministry:
  code: MISE
  name: Ministry
  reporting_timezone: Pacific/Tarawa
departments:
  - code: ABED
    name: Architectural Building
folder_rules:
  project_folder_pattern: "{registry_file_ref} - {project_name}"
  no_overwrite: true
  allowed_operation_types:
    - CREATE_PROJECT_FOLDER
    - DELETE_PROJECT_FOLDER
""",
        encoding="utf-8",
    )

    with pytest.raises(BlueprintParseError, match="Unknown or risky operation"):
        BlueprintParser().parse(path)


def test_blueprint_parser_converts_blueprint_to_plan_operations() -> None:
    blueprint = BlueprintParser().parse(BLUEPRINT_PATH)
    plan = BlueprintParser().to_plan(blueprint, blueprint_path=BLUEPRINT_PATH)

    operation_types = {operation.operation_type for operation in plan.operations}
    targets = {operation.target for operation in plan.operations}

    assert OperationType.CREATE_REPORT_FOLDER in operation_types
    assert OperationType.CREATE_DATABASE_RECORD in operation_types
    assert "standard_sheet_blueprint:TIR Register" in targets
    assert plan.operation_count == len(plan.operations)


def test_dry_run_planner_uses_blueprint_parser_operations() -> None:
    plan = DryRunPlanner().build_plan(blueprint_path=BLUEPRINT_PATH)

    assert any(
        operation.target == "standard_sheet_blueprint:TIR Register"
        for operation in plan.operations
    )
