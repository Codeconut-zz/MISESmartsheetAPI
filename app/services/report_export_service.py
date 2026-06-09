"""Management reporting export service."""

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict

from app.connectors.mise_filesystem import FolderInventoryEntry
from app.domain.tir import TechnicalIntakeRequest
from app.services.data_quality_service import DataQualityService, data_quality_issue_rows
from app.services.reconciliation_service import (
    ReconciliationResult,
    load_folder_inventory_export,
    load_tir_records_export,
)

SUMMARY_SHEET = "Summary"
TIR_SHEET = "TIR Records"
FOLDER_SHEET = "Folder Inventory"
RECONCILIATION_SHEET = "Reconciliation Results"
DATA_QUALITY_SHEET = "Data Quality Issues"


class ReportExportResult(BaseModel):
    """Paths written by a report export run."""

    model_config = ConfigDict(frozen=True)

    xlsx_path: str
    json_path: str
    csv_path: str
    summary_rows: int


class ReportExportService:
    """Generate reporting outputs for management and partner reporting."""

    def __init__(self, *, timestamp: datetime | None = None) -> None:
        self._timestamp = timestamp

    def export(
        self,
        *,
        tir_path: str | Path,
        folders_path: str | Path,
        reconciliation_path: str | Path,
        out_dir: str | Path,
    ) -> ReportExportResult:
        """Generate timestamped JSON, CSV, and XLSX reporting outputs."""
        tir_records = load_tir_records_export(tir_path)
        folder_inventory = load_folder_inventory_export(folders_path)
        reconciliation_results = load_reconciliation_results(reconciliation_path)
        data_quality_report = DataQualityService().check(tir_records)
        summary_rows = build_summary_rows(tir_records, reconciliation_results)
        output_dir = Path(out_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"mise_report_{self._timestamp_string()}"

        xlsx_path = output_dir / f"{stem}.xlsx"
        json_path = output_dir / f"{stem}.json"
        csv_path = output_dir / f"{stem}_summary.csv"

        _write_xlsx(
            xlsx_path,
            summary_rows=summary_rows,
            tir_records=tir_records,
            folder_inventory=folder_inventory,
            reconciliation_results=reconciliation_results,
            data_quality_issues=data_quality_issue_rows(data_quality_report),
        )
        _write_json(
            json_path,
            summary_rows=summary_rows,
            tir_records=tir_records,
            folder_inventory=folder_inventory,
            reconciliation_results=reconciliation_results,
            data_quality_issues=data_quality_issue_rows(data_quality_report),
        )
        pd.DataFrame(summary_rows).to_csv(csv_path, index=False)

        return ReportExportResult(
            xlsx_path=str(xlsx_path),
            json_path=str(json_path),
            csv_path=str(csv_path),
            summary_rows=len(summary_rows),
        )

    def _timestamp_string(self) -> str:
        timestamp = self._timestamp or datetime.now(UTC)
        return timestamp.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def load_reconciliation_results(path: str | Path) -> list[ReconciliationResult]:
    """Load reconciliation results from JSON, CSV, or XLSX."""
    input_path = Path(path)
    suffix = input_path.suffix.lower()
    if suffix == ".xlsx":
        rows = pd.read_excel(input_path).to_dict(orient="records")
    elif suffix == ".csv":
        rows = pd.read_csv(input_path).to_dict(orient="records")
    else:
        rows = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(rows, list):
        raise ValueError("Reconciliation export must contain a list of result rows")

    return [ReconciliationResult.model_validate(_normalize_reconciliation_row(row)) for row in rows]


def build_summary_rows(
    tir_records: list[TechnicalIntakeRequest],
    reconciliation_results: list[ReconciliationResult],
) -> list[dict[str, Any]]:
    """Build normalized summary count rows."""
    summary_rows: list[dict[str, Any]] = []
    summary_rows.extend(_count_rows("project_status", [record.project_status for record in tir_records]))
    summary_rows.extend(_count_rows("funding_source", [record.funding_source for record in tir_records]))
    summary_rows.extend(_count_rows("department_hod", [record.mise_hod for record in tir_records]))
    summary_rows.extend(_count_rows("service_request", [record.service_request for record in tir_records]))
    summary_rows.extend(_count_rows("project_location", [record.project_location for record in tir_records]))
    summary_rows.extend(
        _count_rows(
            "reconciliation_category",
            [result.category for result in reconciliation_results],
        )
    )
    return summary_rows


def _write_xlsx(
    output_path: Path,
    *,
    summary_rows: list[dict[str, Any]],
    tir_records: list[TechnicalIntakeRequest],
    folder_inventory: list[FolderInventoryEntry],
    reconciliation_results: list[ReconciliationResult],
    data_quality_issues: list[dict[str, Any]],
) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name=SUMMARY_SHEET, index=False)
        pd.DataFrame([record.model_dump(mode="json") for record in tir_records]).to_excel(
            writer,
            sheet_name=TIR_SHEET,
            index=False,
        )
        pd.DataFrame([folder.model_dump(mode="json") for folder in folder_inventory]).to_excel(
            writer,
            sheet_name=FOLDER_SHEET,
            index=False,
        )
        reconciliation_rows = [_reconciliation_row(result) for result in reconciliation_results]
        pd.DataFrame(reconciliation_rows).to_excel(
            writer,
            sheet_name=RECONCILIATION_SHEET,
            index=False,
        )
        pd.DataFrame(data_quality_issues).to_excel(
            writer,
            sheet_name=DATA_QUALITY_SHEET,
            index=False,
        )


def _write_json(
    output_path: Path,
    *,
    summary_rows: list[dict[str, Any]],
    tir_records: list[TechnicalIntakeRequest],
    folder_inventory: list[FolderInventoryEntry],
    reconciliation_results: list[ReconciliationResult],
    data_quality_issues: list[dict[str, Any]],
) -> None:
    payload = {
        "summary": summary_rows,
        "tir_records": [record.model_dump(mode="json") for record in tir_records],
        "folder_inventory": [folder.model_dump(mode="json") for folder in folder_inventory],
        "reconciliation_results": [_reconciliation_row(result) for result in reconciliation_results],
        "data_quality_issues": data_quality_issues,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _count_rows(section: str, values: list[str]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        label = value or "UNSPECIFIED"
        counts[label] = counts.get(label, 0) + 1

    return [
        {"section": section, "value": value, "count": count}
        for value, count in sorted(counts.items())
    ]


def _reconciliation_row(result: ReconciliationResult) -> dict[str, Any]:
    row = result.model_dump(mode="json")
    row["reasons"] = "; ".join(result.reasons)
    return row


def _normalize_reconciliation_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError("Reconciliation row must be an object")

    normalized = dict(row)
    reasons = normalized.get("reasons", [])
    if isinstance(reasons, str):
        normalized["reasons"] = [reason.strip() for reason in reasons.split(";") if reason.strip()]
    return normalized
