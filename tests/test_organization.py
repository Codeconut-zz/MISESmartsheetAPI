import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from app.cli.main import app
from app.domain.organization import Department, Division, ReportingLine, Role
from app.services.organization_loader import load_organization_blueprint

BLUEPRINT_PATH = Path("config/architecture/mise_ministry_blueprint.example.yaml")
runner = CliRunner()


def test_organization_models_validate_required_fields() -> None:
    role = Role(code="DIRECTOR_ABED", title="Director ABED")
    division = Division(code="ADD", name="Architectural Design Division", head_role="Principal")
    department = Department(
        code="ABED",
        name="Architectural Building & Engineering Department",
        director_role_code=role.code,
        divisions=[division],
    )
    line = ReportingLine(supervisor_role_code="DG_ENGINEERING", report_role_code=role.code)

    assert department.divisions == [division]
    assert line.report_role_code == "DIRECTOR_ABED"


def test_blueprint_abed_has_exactly_four_divisions() -> None:
    blueprint = load_organization_blueprint(BLUEPRINT_PATH)

    abed = blueprint.department_by_code("ABED")

    assert len(abed.divisions) == 4
    assert {division.code for division in abed.divisions} == {"ADD", "CPD", "QCID", "BMD"}


def test_all_departments_have_codes_and_names() -> None:
    blueprint = load_organization_blueprint(BLUEPRINT_PATH)

    assert blueprint.departments
    assert all(department.code and department.name for department in blueprint.departments)


def test_cli_validates_blueprint() -> None:
    result = runner.invoke(app, ["org", "validate-blueprint", str(BLUEPRINT_PATH)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "valid"
    assert payload["blueprint"]["department_count"] == 5


def test_cli_rejects_invalid_blueprint(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.yaml"
    invalid_path.write_text("departments: []\n", encoding="utf-8")

    result = runner.invoke(app, ["org", "validate-blueprint", str(invalid_path)])

    assert result.exit_code == 1
    payload: dict[str, Any] = json.loads(result.stderr)
    assert "Blueprint validation failed" in payload["error"]
