"""Read-only TIR pull workflow."""

from collections.abc import Callable
from contextlib import AbstractContextManager
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.tir import TechnicalIntakeRequest
from app.services.tir_mapper import TIRMapper, TIRMappingError
from app.storage.repositories import TIRRecordRepository


class TIRPullError(ValueError):
    """Raised when TIR pulling cannot complete."""


class InvalidTIRRow(BaseModel):
    """Details for a Smartsheet row that failed TIR validation."""

    model_config = ConfigDict(frozen=True)

    row_id: str
    error: str


class TIRPullSummary(BaseModel):
    """Summary of a TIR pull."""

    model_config = ConfigDict(frozen=True)

    rows_read: int
    rows_valid: int
    rows_invalid: int
    missing_columns: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rows_persisted: int = 0


class TIRPullResult(BaseModel):
    """Full TIR pull result."""

    model_config = ConfigDict(frozen=True)

    summary: TIRPullSummary
    raw: dict[str, Any]
    normalized: list[TechnicalIntakeRequest]
    invalid_rows: list[InvalidTIRRow]

    def to_export_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable export payload."""
        return self.model_dump(mode="json")


class TIRPullService:
    """Pull, validate, optionally persist, and optionally export TIR rows."""

    def __init__(
        self,
        *,
        smartsheet_client: Any,
        mapper: TIRMapper | None = None,
        repository: TIRRecordRepository | None = None,
        session_scope_factory: Callable[[], AbstractContextManager[Session]] | None = None,
    ) -> None:
        self._smartsheet_client = smartsheet_client
        self._mapper = mapper or TIRMapper()
        self._repository = repository or TIRRecordRepository()
        self._session_scope_factory = session_scope_factory

    def pull(
        self,
        *,
        sheet_id: str,
        persist: bool = False,
        out: str | Path | None = None,
        pretty: bool = False,
    ) -> TIRPullResult:
        """Pull and normalize TIR rows from a Smartsheet sheet."""
        if not sheet_id:
            raise TIRPullError("A TIR sheet ID is required")

        sheet = self._smartsheet_client.get_sheet(sheet_id)
        columns = _list_from_sheet(sheet, "columns")
        rows = _list_from_sheet(sheet, "rows")
        missing_columns = self._mapper.missing_columns(columns)
        warnings: list[str] = []
        normalized: list[TechnicalIntakeRequest] = []
        valid_pairs: list[tuple[dict[str, Any], TechnicalIntakeRequest]] = []
        invalid_rows: list[InvalidTIRRow] = []

        if not rows:
            warnings.append("No rows returned from Smartsheet sheet")

        for row in rows:
            try:
                record = self._mapper.map_row(row=row, columns=columns)
                normalized.append(record)
                valid_pairs.append((row, record))
            except TIRMappingError as exc:
                invalid_rows.append(InvalidTIRRow(row_id=str(row.get("id", "")), error=str(exc)))

        rows_persisted = self._persist_records(sheet_id, valid_pairs) if persist else 0
        result = TIRPullResult(
            summary=TIRPullSummary(
                rows_read=len(rows),
                rows_valid=len(normalized),
                rows_invalid=len(invalid_rows),
                missing_columns=missing_columns,
                warnings=warnings,
                rows_persisted=rows_persisted,
            ),
            raw={"columns": columns, "rows": rows},
            normalized=normalized,
            invalid_rows=invalid_rows,
        )

        if out is not None:
            _write_export(result, out=out, pretty=pretty)

        return result

    def _persist_records(
        self,
        sheet_id: str,
        records: list[tuple[dict[str, Any], TechnicalIntakeRequest]],
    ) -> int:
        if self._session_scope_factory is None:
            raise TIRPullError("Persistence requested but no database session scope is configured")

        with self._session_scope_factory() as session:
            for row, record in records:
                self._repository.add(
                    session,
                    record,
                    smartsheet_sheet_id=sheet_id,
                    smartsheet_row_id=str(row.get("id", "")),
                )

        return len(records)


def _list_from_sheet(sheet: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = sheet.get(key, [])
    if not isinstance(value, list):
        raise TIRPullError(f"Smartsheet sheet field '{key}' must be a list")

    return [item for item in value if isinstance(item, dict)]


def _write_export(result: TIRPullResult, *, out: str | Path, pretty: bool) -> None:
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(result.to_export_payload(), indent=indent, sort_keys=pretty),
        encoding="utf-8",
    )
