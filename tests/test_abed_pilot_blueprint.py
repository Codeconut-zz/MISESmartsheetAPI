from pathlib import Path

from app.domain.plan import OperationType
from app.services.blueprint_parser import BlueprintParser
from app.services.dry_run_planner import DryRunPlanner
from app.services.organization_loader import load_organization_blueprint

BLUEPRINT_PATH = Path("config/architecture/abed_pilot_blueprint.yaml")


def test_abed_pilot_blueprint_validates_with_organization_loader() -> None:
    blueprint = load_organization_blueprint(BLUEPRINT_PATH)

    assert [department.code for department in blueprint.departments] == ["ABED"]
    assert {division.code for division in blueprint.department_by_code("ABED").divisions} == {
        "ADD",
        "CPD",
        "QCID",
        "BMD",
    }


def test_abed_pilot_blueprint_parser_has_pilot_folders_and_reports() -> None:
    blueprint = BlueprintParser().parse(BLUEPRINT_PATH)

    assert blueprint.standard_folders == [
        "01 - Intake",
        "02 - Active Projects",
        "03 - Project Files",
        "04 - Reports",
        "05 - Archive",
    ]
    assert "director_abed_summary" in blueprint.reporting_outputs
    assert "abed_bmd_division_summary" in blueprint.reporting_outputs


def test_abed_pilot_blueprint_has_no_write_operations_by_default() -> None:
    blueprint = BlueprintParser().parse(BLUEPRINT_PATH)

    assert blueprint.folder_rules.allowed_operation_types == []
    assert blueprint.smartsheet_writeback_rules.allowed_columns == []


def test_abed_pilot_dry_run_plan_contains_only_safe_operation_types() -> None:
    plan = DryRunPlanner().build_plan(blueprint_path=BLUEPRINT_PATH)
    operation_types = {operation.operation_type for operation in plan.operations}

    assert OperationType.CREATE_REPORT_FOLDER in operation_types
    assert OperationType.CREATE_DATABASE_RECORD in operation_types
    assert OperationType.UPDATE_SMARTSHEET_ROW not in operation_types
    assert OperationType.ADD_SMARTSHEET_ATTACHMENT_LINK not in operation_types
    assert OperationType.CREATE_PROJECT_FOLDER not in operation_types
