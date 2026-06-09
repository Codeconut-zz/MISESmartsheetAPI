"""Data quality checks for normalized TIR records."""

from pathlib import Path
import json
from collections.abc import Iterable
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from app.domain.tir import PROJECT_STATUSES, TechnicalIntakeRequest

IssueSeverity = Literal["INFO", "WARNING", "ERROR"]

REQUIRED_CHECKS = (
    "missing_project_name",
    "missing_contact_email",
    "missing_registry_file_reference",
    "missing_funding_source",
    "invalid_project_status",
    "missing_service_request",
    "missing_project_location",
    "missing_secretary_approval_value",
    "missing_registry_confirmation_value",
)


class DataQualityIssue(BaseModel):
    """One data-quality issue."""

    model_config = ConfigDict(frozen=True)

    record_key: str
    issue_type: str
    severity: IssueSeverity
    message: str


class RecordDataQualityResult(BaseModel):
    """Data-quality result for one TIR record."""

    model_config = ConfigDict(frozen=True)

    record_key: str
    project_name: str
    registry_file_ref: str
    completeness_score: int = Field(ge=0, le=100)
    issues: list[DataQualityIssue]


class DataQualitySummary(BaseModel):
    """Aggregate data-quality summary."""

    model_config = ConfigDict(frozen=True)

    total_records: int
    issue_counts: dict[str, int]
    severity_counts: dict[str, int]
    average_completeness_score: float


class DataQualityReport(BaseModel):
    """Full data-quality report."""

    model_config = ConfigDict(frozen=True)

    summary: DataQualitySummary
    records: list[RecordDataQualityResult]

    @property
    def issues(self) -> list[DataQualityIssue]:
        """Return all issues across all records."""
        return [issue for record in self.records for issue in record.issues]


class DataQualityService:
    """Evaluate explicit data-quality rules."""

    def check(self, records: list[TechnicalIntakeRequest]) -> DataQualityReport:
        """Run data-quality checks for TIR records."""
        record_results = [self._check_record(record) for record in records]
        all_issues = [issue for result in record_results for issue in result.issues]
        issue_counts = _counts(issue.issue_type for issue in all_issues)
        severity_counts = _counts(issue.severity for issue in all_issues)
        average_score = (
            sum(result.completeness_score for result in record_results) / len(record_results)
            if record_results
            else 100.0
        )

        return DataQualityReport(
            summary=DataQualitySummary(
                total_records=len(record_results),
                issue_counts=issue_counts,
                severity_counts=severity_counts,
                average_completeness_score=round(average_score, 2),
            ),
            records=record_results,
        )

    def _check_record(self, record: TechnicalIntakeRequest) -> RecordDataQualityResult:
        issues: list[DataQualityIssue] = []
        record_key = _record_key(record)

        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="project_name",
            issue_type="missing_project_name",
            severity="ERROR",
            label="project name",
        )
        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="contact_email",
            issue_type="missing_contact_email",
            severity="ERROR",
            label="contact email",
        )
        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="registry_file_ref",
            issue_type="missing_registry_file_reference",
            severity="WARNING",
            label="registry file reference",
        )
        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="funding_source",
            issue_type="missing_funding_source",
            severity="WARNING",
            label="funding source",
        )
        _add_invalid_status_issue(issues, record_key=record_key, record=record)
        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="service_request",
            issue_type="missing_service_request",
            severity="WARNING",
            label="service request",
        )
        _add_missing_text_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="project_location",
            issue_type="missing_project_location",
            severity="WARNING",
            label="project location",
        )
        _add_missing_value_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="secretary_approval",
            issue_type="missing_secretary_approval_value",
            label="secretary approval",
        )
        _add_missing_value_issue(
            issues,
            record_key=record_key,
            record=record,
            field_name="registry_confirmation",
            issue_type="missing_registry_confirmation_value",
            label="registry confirmation",
        )

        passed_checks = len(REQUIRED_CHECKS) - len({issue.issue_type for issue in issues})
        completeness_score = round((passed_checks / len(REQUIRED_CHECKS)) * 100)
        return RecordDataQualityResult(
            record_key=record_key,
            project_name=str(getattr(record, "project_name", "") or ""),
            registry_file_ref=str(getattr(record, "registry_file_ref", "") or ""),
            completeness_score=completeness_score,
            issues=issues,
        )


def export_data_quality_report(report: DataQualityReport, out: str | Path) -> None:
    """Export a data-quality report as XLSX, CSV, or JSON."""
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    issue_rows = [issue.model_dump(mode="json") for issue in report.issues]
    record_rows = [record.model_dump(mode="json", exclude={"issues"}) for record in report.records]
    summary_rows = [
        {"section": "issue_type", "value": key, "count": value}
        for key, value in sorted(report.summary.issue_counts.items())
    ] + [
        {"section": "severity", "value": key, "count": value}
        for key, value in sorted(report.summary.severity_counts.items())
    ]

    if output_path.suffix.lower() == ".xlsx":
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)
            pd.DataFrame(issue_rows).to_excel(writer, sheet_name="Issues", index=False)
            pd.DataFrame(record_rows).to_excel(writer, sheet_name="Records", index=False)
        return
    if output_path.suffix.lower() == ".csv":
        pd.DataFrame(issue_rows).to_csv(output_path, index=False)
        return

    payload = {
        "summary": report.summary.model_dump(mode="json"),
        "records": [record.model_dump(mode="json") for record in report.records],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def data_quality_issue_rows(report: DataQualityReport) -> list[dict[str, Any]]:
    """Return issue rows for report workbook integration."""
    rows = [issue.model_dump(mode="json") for issue in report.issues]
    return rows or [{"record_key": "", "issue_type": "", "severity": "", "message": ""}]


def _add_missing_text_issue(
    issues: list[DataQualityIssue],
    *,
    record_key: str,
    record: TechnicalIntakeRequest,
    field_name: str,
    issue_type: str,
    severity: IssueSeverity,
    label: str,
) -> None:
    if not str(getattr(record, field_name, "") or "").strip():
        issues.append(
            DataQualityIssue(
                record_key=record_key,
                issue_type=issue_type,
                severity=severity,
                message=f"TIR record is missing {label}",
            )
        )


def _add_missing_value_issue(
    issues: list[DataQualityIssue],
    *,
    record_key: str,
    record: TechnicalIntakeRequest,
    field_name: str,
    issue_type: str,
    label: str,
) -> None:
    if getattr(record, field_name, None) is None:
        issues.append(
            DataQualityIssue(
                record_key=record_key,
                issue_type=issue_type,
                severity="WARNING",
                message=f"TIR record is missing {label} value",
            )
        )


def _add_invalid_status_issue(
    issues: list[DataQualityIssue],
    *,
    record_key: str,
    record: TechnicalIntakeRequest,
) -> None:
    status = str(getattr(record, "project_status", "") or "").strip()
    if status not in PROJECT_STATUSES:
        issues.append(
            DataQualityIssue(
                record_key=record_key,
                issue_type="invalid_project_status",
                severity="ERROR",
                message=f"TIR record has invalid project status: {status or 'missing'}",
            )
        )


def _record_key(record: TechnicalIntakeRequest) -> str:
    return (
        str(getattr(record, "registry_file_ref", "") or "").strip()
        or str(getattr(record, "project_name", "") or "").strip()
        or "unknown-record"
    )


def _counts(values: Iterable[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        label = str(value)
        counts[label] = counts.get(label, 0) + 1
    return counts
