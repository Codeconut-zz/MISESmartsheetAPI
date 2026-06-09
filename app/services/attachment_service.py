"""Smartsheet attachment metadata and guarded download handling."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.connectors.smartsheet_client import SmartsheetClient
from app.storage.repositories import AttachmentMetadataRepository


class AttachmentHandlingError(ValueError):
    """Raised when attachment metadata or download handling is unsafe."""


class AttachmentMetadata(BaseModel):
    """Smartsheet attachment metadata stored without file contents."""

    model_config = ConfigDict(frozen=True)

    attachment_id: str
    name: str
    size: int = Field(ge=0)
    content_type: str = ""
    source_url: str = ""
    tir_record_id: str = ""
    smartsheet_sheet_id: str
    smartsheet_row_id: str
    sanitized_filename: str


class AttachmentMetadataResult(BaseModel):
    """Metadata-only attachment retrieval result."""

    model_config = ConfigDict(frozen=True)

    sheet_id: str
    row_id: str
    metadata_only: bool = True
    attachments: list[AttachmentMetadata]
    persisted_count: int = 0


class AttachmentDownloadResult(BaseModel):
    """Summary of an explicit attachment download."""

    model_config = ConfigDict(frozen=True)

    attachment_id: str
    path: str
    bytes_written: int


class AttachmentService:
    """Read attachment metadata and optionally download files through a gated path."""

    def __init__(
        self,
        *,
        smartsheet_client: SmartsheetClient,
        settings: Settings | None = None,
        repository: AttachmentMetadataRepository | None = None,
        session_scope_factory: Callable[[], AbstractContextManager[Session]] | None = None,
    ) -> None:
        self._smartsheet_client = smartsheet_client
        self._settings = settings or get_settings()
        self._repository = repository or AttachmentMetadataRepository()
        self._session_scope_factory = session_scope_factory

    def list_row_metadata(
        self,
        *,
        sheet_id: str,
        row_id: str,
        tir_record_id: str = "",
        persist: bool = False,
    ) -> AttachmentMetadataResult:
        """Return row attachment metadata without downloading file contents."""
        raw_attachments = self._smartsheet_client.list_row_attachments(sheet_id, row_id)
        attachments = [
            _metadata_from_raw(
                raw_attachment,
                sheet_id=sheet_id,
                row_id=row_id,
                tir_record_id=tir_record_id,
            )
            for raw_attachment in raw_attachments
        ]
        persisted_count = self._persist_metadata(attachments) if persist else 0
        return AttachmentMetadataResult(
            sheet_id=sheet_id,
            row_id=row_id,
            attachments=attachments,
            persisted_count=persisted_count,
        )

    def download_attachment(
        self,
        *,
        sheet_id: str,
        attachment_id: str,
        target_folder: str | Path,
        apply_download: bool,
    ) -> AttachmentDownloadResult:
        """Download one attachment only when download controls are explicit."""
        if not self._settings.features.enable_attachment_downloads:
            raise AttachmentHandlingError("ENABLE_ATTACHMENT_DOWNLOADS=true is required")
        if not apply_download:
            raise AttachmentHandlingError("Explicit --apply-download is required")

        metadata = _metadata_from_raw(
            self._smartsheet_client.get_attachment_metadata(sheet_id, attachment_id),
            sheet_id=sheet_id,
            row_id="",
            tir_record_id="",
        )
        if not metadata.source_url:
            raise AttachmentHandlingError(f"Attachment {attachment_id} does not include a source URL")

        output_dir = _safe_target_folder(target_folder, self._settings)
        content = self._smartsheet_client.download_attachment_content(metadata.source_url)
        output_path = output_dir / metadata.sanitized_filename
        output_path.write_bytes(content)
        return AttachmentDownloadResult(
            attachment_id=metadata.attachment_id,
            path=str(output_path),
            bytes_written=len(content),
        )

    def _persist_metadata(self, attachments: list[AttachmentMetadata]) -> int:
        if self._session_scope_factory is None:
            raise AttachmentHandlingError("Persistence requested but no database session scope is configured")

        with self._session_scope_factory() as session:
            for attachment in attachments:
                self._repository.upsert(
                    session,
                    attachment_id=attachment.attachment_id,
                    name=attachment.name,
                    size=attachment.size,
                    content_type=attachment.content_type,
                    source_url=attachment.source_url,
                    tir_record_id=attachment.tir_record_id,
                    smartsheet_sheet_id=attachment.smartsheet_sheet_id,
                    smartsheet_row_id=attachment.smartsheet_row_id,
                    sanitized_filename=attachment.sanitized_filename,
                )

        return len(attachments)


def sanitize_attachment_filename(filename: str) -> str:
    """Return a safe filename for future attachment downloads."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", filename)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    if not sanitized:
        return "attachment"
    if sanitized in {".", ".."}:
        return "attachment"

    return sanitized


def _metadata_from_raw(
    raw_attachment: dict[str, Any],
    *,
    sheet_id: str,
    row_id: str,
    tir_record_id: str,
) -> AttachmentMetadata:
    name = str(raw_attachment.get("name") or raw_attachment.get("attachmentName") or "attachment")
    return AttachmentMetadata(
        attachment_id=str(raw_attachment.get("id", "")),
        name=name,
        size=_attachment_size(raw_attachment),
        content_type=str(raw_attachment.get("mimeType") or raw_attachment.get("contentType") or ""),
        source_url=str(
            raw_attachment.get("url")
            or raw_attachment.get("downloadUrl")
            or raw_attachment.get("sourceUrl")
            or ""
        ),
        tir_record_id=tir_record_id,
        smartsheet_sheet_id=sheet_id,
        smartsheet_row_id=row_id,
        sanitized_filename=sanitize_attachment_filename(name),
    )


def _attachment_size(raw_attachment: dict[str, Any]) -> int:
    value = raw_attachment.get("size") or raw_attachment.get("sizeInKb") or 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_target_folder(target_folder: str | Path, settings: Settings) -> Path:
    safe_root_value = settings.filesystem.attachment_download_root
    if not safe_root_value:
        raise AttachmentHandlingError("ATTACHMENT_DOWNLOAD_ROOT is required for downloads")

    safe_root = Path(safe_root_value).expanduser().resolve()
    target = Path(target_folder).expanduser()
    if not target.is_absolute():
        target = safe_root / target
    target = target.resolve()

    try:
        target.relative_to(safe_root)
    except ValueError as exc:
        raise AttachmentHandlingError("Target folder must be under ATTACHMENT_DOWNLOAD_ROOT") from exc

    target.mkdir(parents=True, exist_ok=True)
    return target
