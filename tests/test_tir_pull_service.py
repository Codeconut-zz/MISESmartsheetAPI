import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from app.cli import main as cli
from app.cli.main import app
from app.services.tir_pull_service import TIRPullService
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base
from app.storage.repositories import TIRRecordRepository

FIXTURE_PATH = Path("tests/fixtures/tir_rows.json")
runner = CliRunner()


class FakeSmartsheetClient:
    def __init__(self, sheet: dict[str, Any]) -> None:
        self.sheet = sheet
        self.sheet_ids: list[str] = []

    def __enter__(self) -> "FakeSmartsheetClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def get_sheet(self, sheet_id: str, **kwargs: Any) -> dict[str, Any]:
        self.sheet_ids.append(sheet_id)
        return self.sheet


def load_sheet() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_tir_pull_reads_and_normalizes_rows() -> None:
    client = FakeSmartsheetClient(load_sheet())
    service = TIRPullService(smartsheet_client=client)

    result = service.pull(sheet_id="sheet-123")

    assert client.sheet_ids == ["sheet-123"]
    assert result.summary.rows_read == 1
    assert result.summary.rows_valid == 1
    assert result.summary.rows_invalid == 0
    assert result.normalized[0].registry_file_ref == "MISE-ABED-001"


def test_tir_pull_reports_invalid_rows() -> None:
    sheet = load_sheet()
    status_cell = next(cell for cell in sheet["rows"][0]["cells"] if cell["columnId"] == 11)
    status_cell["value"] = "not a real status"
    service = TIRPullService(smartsheet_client=FakeSmartsheetClient(sheet))

    result = service.pull(sheet_id="sheet-123")

    assert result.summary.rows_read == 1
    assert result.summary.rows_valid == 0
    assert result.summary.rows_invalid == 1
    assert "Unknown project status" in result.invalid_rows[0].error


def test_tir_pull_reports_missing_columns() -> None:
    sheet = load_sheet()
    sheet["columns"] = [column for column in sheet["columns"] if column["title"] != "CONTACT EMAIL"]
    service = TIRPullService(smartsheet_client=FakeSmartsheetClient(sheet))

    result = service.pull(sheet_id="sheet-123")

    assert result.summary.missing_columns == ["CONTACT EMAIL"]
    assert result.summary.rows_invalid == 1


def test_tir_pull_exports_raw_and_normalized_json(tmp_path: Path) -> None:
    output_path = tmp_path / "tir_rows.json"
    service = TIRPullService(smartsheet_client=FakeSmartsheetClient(load_sheet()))

    result = service.pull(sheet_id="sheet-123", out=output_path, pretty=True)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.summary.rows_valid == 1
    assert payload["summary"]["rows_valid"] == 1
    assert payload["raw"]["rows"][0]["id"] == 1001
    assert payload["normalized"][0]["project_status"] == "IN_PROGRESS"


def test_tir_pull_persists_when_requested() -> None:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = TIRPullService(
        smartsheet_client=FakeSmartsheetClient(load_sheet()),
        session_scope_factory=lambda: session_scope(engine),
    )

    result = service.pull(sheet_id="sheet-123", persist=True)

    assert result.summary.rows_persisted == 1
    with session_scope(engine) as session:
        stored = TIRRecordRepository().get_by_registry_file_ref(session, "MISE-ABED-001")
        assert stored is not None
        assert stored.smartsheet_sheet_id == "sheet-123"


def test_cli_tir_pull_outputs_summary(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: FakeSmartsheetClient(load_sheet()))

    result = runner.invoke(app, ["tir", "pull", "--sheet-id", "sheet-123"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["rows_read"] == 1
    assert payload["rows_valid"] == 1
