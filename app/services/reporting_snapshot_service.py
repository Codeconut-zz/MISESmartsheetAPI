"""Generate and persist department reporting snapshots."""

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.services.data_quality_service import DataQualityService
from app.services.reconciliation_service import ReconciliationResult
from app.storage.repositories import ReportingRepository

TECHNICAL_DEPARTMENTS = ("ABED", "CED", "EPD", "WSED")
ABED_DIVISIONS = {
    "ADD": "Architectural Design Division",
    "CPD": "Cost Planning Division",
    "QCID": "Quality Control & Inspection Division",
    "BMD": "Building Maintenance Division",
}


class ReportingSnapshot(BaseModel):
    """Department reporting snapshot metrics."""

    model_config = ConfigDict(frozen=True)

    scope: str
    snapshot_name: str
    department_code: str = ""
    division_code: str | None = None
    funding_source: str | None = None
    project_count: int
    status_breakdown: dict[str, int]
    funding_source_breakdown: dict[str, int]
    pending_approvals: int
    approved_projects: int
    declined_projects: int
    data_quality_issue_count: int
    missing_data_count: int
    missing_folder_count: int
    service_request_breakdown: dict[str, int]


class ReportingSnapshotService:
    """Build reporting snapshots for MISE leadership and departments."""

    def __init__(
        self,
        *,
        repository: ReportingRepository | None = None,
        session_scope_factory: Callable[[], AbstractContextManager[Session]] | None = None,
    ) -> None:
        self._repository = repository or ReportingRepository()
        self._session_scope_factory = session_scope_factory

    def generate(
        self,
        *,
        tir_records: list[Any],
        reconciliation_results: list[ReconciliationResult],
    ) -> list[ReportingSnapshot]:
        """Generate all required reporting snapshots."""
        snapshots = [
            _snapshot(
                scope="MINISTRY_PORTFOLIO",
                snapshot_name="Ministry-wide portfolio",
                records=tir_records,
                reconciliation_results=reconciliation_results,
            ),
            _snapshot(
                scope="SECRETARY",
                snapshot_name="Secretary view",
                records=tir_records,
                reconciliation_results=reconciliation_results,
            ),
            _snapshot(
                scope="DG_TECHNICAL_DELIVERY",
                snapshot_name="Director General technical delivery view",
                records=_records_for_departments(tir_records, TECHNICAL_DEPARTMENTS),
                reconciliation_results=reconciliation_results,
            ),
        ]

        for department_code in TECHNICAL_DEPARTMENTS:
            snapshots.append(
                _snapshot(
                    scope="DEPARTMENT",
                    snapshot_name=f"{department_code} view",
                    department_code=department_code,
                    records=_records_for_departments(tir_records, (department_code,)),
                    reconciliation_results=reconciliation_results,
                )
            )

        abed_records = _records_for_departments(tir_records, ("ABED",))
        for division_code, division_name in ABED_DIVISIONS.items():
            snapshots.append(
                _snapshot(
                    scope="DIVISION",
                    snapshot_name=f"ABED {division_code} view",
                    department_code="ABED",
                    division_code=division_code,
                    records=_records_for_division(abed_records, division_code, division_name),
                    reconciliation_results=reconciliation_results,
                )
            )

        return snapshots

    def persist(
        self,
        snapshots: list[ReportingSnapshot],
    ) -> list[ReportingSnapshot]:
        """Persist snapshots by replacing the current snapshot set."""
        if self._session_scope_factory is None:
            raise ValueError("Persistence requested but no database session scope is configured")

        rows = [snapshot.model_dump(mode="json") for snapshot in snapshots]
        with self._session_scope_factory() as session:
            self._repository.replace_department_snapshots(session, rows)

        return snapshots


def snapshot_rows(snapshots: list[ReportingSnapshot]) -> list[dict[str, Any]]:
    """Return export rows for reporting snapshots."""
    return [snapshot.model_dump(mode="json") for snapshot in snapshots]


def _snapshot(
    *,
    scope: str,
    snapshot_name: str,
    records: list[Any],
    reconciliation_results: list[ReconciliationResult],
    department_code: str = "",
    division_code: str | None = None,
) -> ReportingSnapshot:
    data_quality_report = DataQualityService().check(records)
    return ReportingSnapshot(
        scope=scope,
        snapshot_name=snapshot_name,
        department_code=department_code,
        division_code=division_code,
        project_count=len(records),
        status_breakdown=_counts(_record_value(record, "project_status") for record in records),
        funding_source_breakdown=_counts(_record_value(record, "funding_source") for record in records),
        pending_approvals=sum(
            1 for record in records if not bool(getattr(record, "secretary_approval", False))
        ),
        approved_projects=sum(
            1
            for record in records
            if _record_value(record, "project_status") == "APPROVED"
            or bool(getattr(record, "secretary_approval", False))
        ),
        declined_projects=sum(
            1 for record in records if _record_value(record, "project_status") == "DECLINED"
        ),
        data_quality_issue_count=len(data_quality_report.issues),
        missing_data_count=len(data_quality_report.issues),
        missing_folder_count=_missing_folder_count(records, reconciliation_results),
        service_request_breakdown=_counts(_record_value(record, "service_request") for record in records),
    )


def _records_for_departments(records: list[Any], department_codes: Iterable[str]) -> list[Any]:
    department_set = set(department_codes)
    return [record for record in records if _record_value(record, "mise_hod") in department_set]


def _records_for_division(records: list[Any], division_code: str, division_name: str) -> list[Any]:
    needles = {division_code.lower(), division_name.lower()}
    return [
        record
        for record in records
        if any(needle in _division_search_text(record) for needle in needles)
    ]


def _division_search_text(record: Any) -> str:
    return " ".join(
        [
            _record_value(record, "service_request"),
            _record_value(record, "project_name"),
            _record_value(record, "project_background_information"),
        ]
    ).lower()


def _missing_folder_count(
    records: list[Any],
    reconciliation_results: list[ReconciliationResult],
) -> int:
    scoped_refs = {_record_value(record, "registry_file_ref") for record in records}
    scoped_names = {_record_value(record, "project_name") for record in records}
    return sum(
        1
        for result in reconciliation_results
        if result.category == "MISSING_FOLDER"
        and (result.registry_file_ref in scoped_refs or result.project_name in scoped_names)
    )


def _record_value(record: Any, field_name: str) -> str:
    return str(getattr(record, field_name, "") or "").strip()


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        label = value or "UNSPECIFIED"
        counts[label] = counts.get(label, 0) + 1

    return counts
