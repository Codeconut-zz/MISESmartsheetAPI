import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from typer.testing import CliRunner

from app.cli import main as cli
from app.cli.main import app
from app.config import Settings, SmartsheetSettings, get_settings
from app.connectors.smartsheet_client import SmartsheetClient
from app.services.attachment_service import (
    AttachmentHandlingError,
    AttachmentService,
    sanitize_attachment_filename,
)
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base
from app.storage.repositories import AttachmentMetadataRepository

BASE_URL = "https://api.smartsheet.test/2.0"
TOKEN = "test-token-value"
runner = CliRunner()


class FakeAttachmentClient:
    def __init__(self) -> None:
        self.download_calls: list[str] = []
        self.list_calls: list[tuple[str, str]] = []

    def __enter__(self) -> "FakeAttachmentClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def list_row_attachments(self, sheet_id: str, row_id: str) -> list[dict[str, Any]]:
        self.list_calls.append((sheet_id, row_id))
        return [
            {
                "id": "att-1",
                "name": 'Official: Request/Letter?.pdf',
                "size": 2048,
                "mimeType": "application/pdf",
                "url": "https://download.example.test/att-1",
            }
        ]

    def get_attachment_metadata(self, sheet_id: str, attachment_id: str) -> dict[str, Any]:
        return {
            "id": attachment_id,
            "name": "Official Letter.pdf",
            "size": 1024,
            "mimeType": "application/pdf",
            "url": "https://download.example.test/att-1",
        }

    def download_attachment_content(self, source_url: str) -> bytes:
        self.download_calls.append(source_url)
        return b"pdf-bytes"


@respx.mock
def test_client_lists_row_attachments_metadata_only() -> None:
    route = respx.get(
        f"{BASE_URL}/sheets/sheet-123/rows/row-456/attachments",
        params={"pageSize": 100, "page": 1},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"totalPages": 1, "data": [{"id": "att-1", "name": "letter.pdf"}]},
        )
    )
    client = SmartsheetClient(
        settings=SmartsheetSettings(base_url=BASE_URL, access_token=TOKEN, tir_sheet_id="sheet-123")
    )

    with client:
        attachments = client.list_row_attachments("sheet-123", "row-456")

    assert attachments == [{"id": "att-1", "name": "letter.pdf"}]
    assert route.calls[0].request.method == "GET"


@respx.mock
def test_client_gets_attachment_metadata_without_content_download() -> None:
    metadata_route = respx.get(f"{BASE_URL}/sheets/sheet-123/attachments/att-1").mock(
        return_value=httpx.Response(200, json={"id": "att-1", "name": "letter.pdf"})
    )
    download_route = respx.get("https://download.example.test/att-1").mock(
        return_value=httpx.Response(200, content=b"file")
    )
    client = SmartsheetClient(
        settings=SmartsheetSettings(base_url=BASE_URL, access_token=TOKEN, tir_sheet_id="sheet-123")
    )

    with client:
        metadata = client.get_attachment_metadata("sheet-123", "att-1")

    assert metadata == {"id": "att-1", "name": "letter.pdf"}
    assert metadata_route.called
    assert not download_route.called


def test_attachment_service_returns_metadata_and_safe_filename() -> None:
    client = FakeAttachmentClient()
    service = AttachmentService(smartsheet_client=client)

    result = service.list_row_metadata(
        sheet_id="sheet-123",
        row_id="row-456",
        tir_record_id="tir-1",
    )

    assert result.metadata_only is True
    assert result.attachments[0].attachment_id == "att-1"
    assert result.attachments[0].sanitized_filename == "Official- Request-Letter-.pdf"
    assert client.download_calls == []


def test_attachment_service_persists_metadata_only(tmp_path: Path) -> None:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = AttachmentService(
        smartsheet_client=FakeAttachmentClient(),
        session_scope_factory=lambda: session_scope(engine),
    )

    result = service.list_row_metadata(
        sheet_id="sheet-123",
        row_id="row-456",
        tir_record_id="tir-1",
        persist=True,
    )

    with session_scope(engine) as session:
        stored = AttachmentMetadataRepository().list_by_tir_record(session, "tir-1")

    assert result.persisted_count == 1
    assert stored[0].attachment_id == "att-1"
    assert stored[0].sanitized_filename == "Official- Request-Letter-.pdf"


def test_attachment_download_requires_feature_flag_and_apply(tmp_path: Path) -> None:
    service = AttachmentService(
        smartsheet_client=FakeAttachmentClient(),
        settings=Settings(
            environment="test",
            enable_attachment_downloads=False,
            attachment_download_root=str(tmp_path),
            _env_file=None,
        ),
    )

    with pytest.raises(AttachmentHandlingError, match="ENABLE_ATTACHMENT_DOWNLOADS"):
        service.download_attachment(
            sheet_id="sheet-123",
            attachment_id="att-1",
            target_folder=tmp_path,
            apply_download=True,
        )

    service = AttachmentService(
        smartsheet_client=FakeAttachmentClient(),
        settings=Settings(
            environment="test",
            enable_attachment_downloads=True,
            attachment_download_root=str(tmp_path),
            _env_file=None,
        ),
    )
    with pytest.raises(AttachmentHandlingError, match="--apply-download"):
        service.download_attachment(
            sheet_id="sheet-123",
            attachment_id="att-1",
            target_folder=tmp_path,
            apply_download=False,
        )


def test_attachment_download_sanitizes_filename_under_safe_root(tmp_path: Path) -> None:
    client = FakeAttachmentClient()
    service = AttachmentService(
        smartsheet_client=client,
        settings=Settings(
            environment="test",
            enable_attachment_downloads=True,
            attachment_download_root=str(tmp_path),
            _env_file=None,
        ),
    )

    result = service.download_attachment(
        sheet_id="sheet-123",
        attachment_id="att-1",
        target_folder="requests",
        apply_download=True,
    )

    assert Path(result.path).read_bytes() == b"pdf-bytes"
    assert Path(result.path).name == "Official Letter.pdf"
    assert Path(result.path).parent == tmp_path / "requests"


def test_attachment_filename_sanitization() -> None:
    assert sanitize_attachment_filename('bad:name/with*chars?.pdf') == "bad-name-with-chars-.pdf"
    assert sanitize_attachment_filename(" .. ") == "attachment"


def test_tir_attachments_cli_metadata_only(
    monkeypatch: Any,
) -> None:
    client = FakeAttachmentClient()
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: client)
    get_settings.cache_clear()

    result = runner.invoke(
        app,
        [
            "tir",
            "attachments",
            "--sheet-id",
            "sheet-123",
            "--row-id",
            "row-456",
            "--metadata-only",
        ],
    )

    get_settings.cache_clear()
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["metadata_only"] is True
    assert payload["attachments"][0]["attachment_id"] == "att-1"
    assert client.download_calls == []
