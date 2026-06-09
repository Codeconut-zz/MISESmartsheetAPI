"""Scheduled read-only polling workflow."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.audit_service import AuditService, audit_service
from app.services.tir_mapper import TIRMapper, TIRMappingError
from app.storage.repositories import TIRRecordRepository


class PollingError(ValueError):
    """Raised when polling cannot run safely."""


class PollingResult(BaseModel):
    """Summary of one polling run."""

    model_config = ConfigDict(frozen=True)

    sheet_id: str
    rows_read: int
    rows_valid: int
    rows_invalid: int
    rows_created: int
    rows_updated: int
    rows_unchanged: int
    warnings: list[str] = Field(default_factory=list)


class PollingService:
    """Run read-only Smartsheet polling and local persistence."""

    def __init__(
        self,
        *,
        smartsheet_client: Any,
        session_scope_factory: Callable[[], AbstractContextManager[Session]],
        mapper: TIRMapper | None = None,
        repository: TIRRecordRepository | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._smartsheet_client = smartsheet_client
        self._session_scope_factory = session_scope_factory
        self._mapper = mapper or TIRMapper()
        self._repository = repository or TIRRecordRepository()
        self._audit = audit or audit_service

    def poll_once(self, *, sheet_id: str | None = None) -> PollingResult:
        """Run one read-only polling cycle."""
        effective_sheet_id = sheet_id or get_settings().smartsheet.tir_sheet_id
        if not effective_sheet_id:
            raise PollingError("SMARTSHEET_TIR_SHEET_ID is required for polling")

        sheet = self._smartsheet_client.get_sheet(effective_sheet_id)
        columns = _list_from_sheet(sheet, "columns")
        rows = _list_from_sheet(sheet, "rows")
        created = updated = unchanged = valid = invalid = 0
        warnings: list[str] = []

        with self._session_scope_factory() as session:
            for row in rows:
                try:
                    record = self._mapper.map_row(row=row, columns=columns)
                except TIRMappingError as exc:
                    invalid += 1
                    warnings.append(f"Row {row.get('id', '')}: {exc}")
                    continue

                valid += 1
                _, action = self._repository.upsert_from_smartsheet_row(
                    session,
                    record,
                    smartsheet_sheet_id=effective_sheet_id,
                    smartsheet_row_id=str(row.get("id", "")),
                    smartsheet_modified_at=_parse_modified_at(row),
                )
                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    unchanged += 1

        result = PollingResult(
            sheet_id=effective_sheet_id,
            rows_read=len(rows),
            rows_valid=valid,
            rows_invalid=invalid,
            rows_created=created,
            rows_updated=updated,
            rows_unchanged=unchanged,
            warnings=warnings,
        )
        self._audit.record(
            actor="system",
            action="sync.poll_once",
            target_type="smartsheet_sheet",
            target_id=effective_sheet_id,
            status="success" if invalid == 0 else "warning",
            message="Completed read-only Smartsheet polling",
            metadata=result.model_dump(mode="json"),
            dry_run=False,
        )
        return result


def _parse_modified_at(row: dict[str, Any]) -> datetime | None:
    raw_value = row.get("modifiedAt") or row.get("modified_at")
    if not raw_value:
        return None
    if isinstance(raw_value, datetime):
        return raw_value
    if isinstance(raw_value, str):
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))

    return None


def _list_from_sheet(sheet: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = sheet.get(key, [])
    if not isinstance(value, list):
        raise PollingError(f"Smartsheet sheet field '{key}' must be a list")

    return [item for item in value if isinstance(item, dict)]
