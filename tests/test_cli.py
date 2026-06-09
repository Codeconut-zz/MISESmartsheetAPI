import json
from typing import Any

from typer.testing import CliRunner
from typer.main import Typer

from app.cli import main as cli
from app.cli.main import app
from app.connectors.smartsheet_client import SmartsheetError

runner = CliRunner()


class MockSmartsheetClient:
    def __enter__(self) -> "MockSmartsheetClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def whoami(self) -> dict[str, str]:
        return {"email": "it@example.test"}

    def list_workspaces(self) -> list[dict[str, str]]:
        return [{"id": "workspace-1", "name": "MISE"}]

    def list_sheets(self) -> list[dict[str, str]]:
        return [{"id": "sheet-1", "name": "TIR"}]


class FailingSmartsheetClient(MockSmartsheetClient):
    def whoami(self) -> dict[str, str]:
        raise SmartsheetError("not authorized", status_code=401)


def test_cli_app_imports() -> None:
    assert isinstance(app, Typer)


def test_health_outputs_json() -> None:
    result = runner.invoke(app, ["health"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok"}


def test_health_supports_pretty_json() -> None:
    result = runner.invoke(app, ["health", "--pretty"])

    assert result.exit_code == 0
    assert result.stdout.startswith("{\n")
    assert json.loads(result.stdout) == {"status": "ok"}


def test_smartsheet_whoami_uses_mocked_client(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: MockSmartsheetClient())

    result = runner.invoke(app, ["smartsheet", "whoami"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"email": "it@example.test"}


def test_smartsheet_list_commands_output_json(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: MockSmartsheetClient())

    workspaces = runner.invoke(app, ["smartsheet", "list-workspaces"])
    sheets = runner.invoke(app, ["smartsheet", "list-sheets"])

    assert workspaces.exit_code == 0
    assert json.loads(workspaces.stdout) == {"data": [{"id": "workspace-1", "name": "MISE"}]}
    assert sheets.exit_code == 0
    assert json.loads(sheets.stdout) == {"data": [{"id": "sheet-1", "name": "TIR"}]}


def test_smartsheet_command_reports_missing_token() -> None:
    result = runner.invoke(app, ["smartsheet", "whoami"])

    assert result.exit_code == 1
    assert "SMARTSHEET_ACCESS_TOKEN" in result.stderr


def test_smartsheet_command_reports_auth_failure(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: FailingSmartsheetClient())

    result = runner.invoke(app, ["smartsheet", "whoami"])

    assert result.exit_code == 1
    assert "authentication failed" in result.stderr
