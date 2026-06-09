import copy
import json
from typing import Any

from app.services.audit_service import AuditService, InMemoryAuditSink
from app.services.polling_service import PollingService
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base
from app.storage.repositories import TIRRecordRepository


class FakeSmartsheetClient:
    def __init__(self, sheet: dict[str, Any]) -> None:
        self.sheet = sheet
        self.calls: list[str] = []

    def get_sheet(self, sheet_id: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(sheet_id)
        return copy.deepcopy(self.sheet)


def load_sheet() -> dict[str, Any]:
    sheet = json.loads(open("tests/fixtures/tir_rows.json", encoding="utf-8").read())
    sheet["rows"][0]["id"] = "row-1"
    sheet["rows"][0]["modifiedAt"] = "2026-06-01T09:00:00Z"
    return sheet


def make_service(
    client: FakeSmartsheetClient,
    sink: InMemoryAuditSink,
):
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = PollingService(
        smartsheet_client=client,
        session_scope_factory=lambda: session_scope(engine),
        audit=AuditService(sink=sink),
    )
    return service, engine


def test_polling_is_idempotent_for_same_row_and_modified_timestamp() -> None:
    client = FakeSmartsheetClient(load_sheet())
    sink = InMemoryAuditSink()
    service, engine = make_service(client, sink)

    first = service.poll_once(sheet_id="sheet-123")
    second = service.poll_once(sheet_id="sheet-123")

    assert first.rows_created == 1
    assert second.rows_unchanged == 1
    assert client.calls == ["sheet-123", "sheet-123"]
    assert len(sink.list_events()) == 2
    with session_scope(engine) as session:
        records = TIRRecordRepository().list_all(session)
        assert len(records) == 1
        assert records[0].last_synced_at is not None


def test_polling_updates_changed_row_without_duplicate() -> None:
    sheet = load_sheet()
    client = FakeSmartsheetClient(sheet)
    sink = InMemoryAuditSink()
    service, engine = make_service(client, sink)

    service.poll_once(sheet_id="sheet-123")
    name_cell = next(cell for cell in sheet["rows"][0]["cells"] if cell["columnId"] == 8)
    name_cell["value"] = "Updated community hall roof repair"
    sheet["rows"][0]["modifiedAt"] = "2026-06-01T10:00:00Z"
    result = service.poll_once(sheet_id="sheet-123")

    assert result.rows_updated == 1
    with session_scope(engine) as session:
        records = TIRRecordRepository().list_all(session)
        assert len(records) == 1
        assert records[0].project_name == "Updated community hall roof repair"
