"""Repository layer for persisted application records."""

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domain.tir import TechnicalIntakeRequest
from app.storage.models import (
    DepartmentReportingSnapshot,
    ProjectFolderInventory,
    ReconciliationResult,
    TIRRecord,
    utc_now,
)

SortOrder = Literal["asc", "desc"]


class TIRRecordRepository:
    """Repository for Technical Intake Request records."""

    def add(
        self,
        session: Session,
        tir: TechnicalIntakeRequest,
        *,
        smartsheet_sheet_id: str = "",
        smartsheet_row_id: str = "",
    ) -> TIRRecord:
        """Persist a TIR domain object."""
        record = TIRRecord(
            smartsheet_sheet_id=smartsheet_sheet_id,
            smartsheet_row_id=smartsheet_row_id,
            last_synced_at=utc_now(),
            created=tir.created,
            secretary_approval=tir.secretary_approval,
            mise_hod=tir.mise_hod,
            registry_confirmation=tir.registry_confirmation,
            registry_file_ref=tir.registry_file_ref,
            client_file_ref=tir.client_file_ref,
            organisation=tir.organisation,
            project_name=tir.project_name,
            service_request=tir.service_request,
            project_location=tir.project_location,
            project_status=tir.project_status,
            contact_person=tir.contact_person,
            contact_person_position=tir.contact_person_position,
            contact_number=tir.contact_number,
            contact_email=tir.contact_email,
            project_background_information=tir.project_background_information,
            funding_source=tir.funding_source,
        )
        session.add(record)
        session.flush()
        return record

    def upsert_from_smartsheet_row(
        self,
        session: Session,
        tir: TechnicalIntakeRequest,
        *,
        smartsheet_sheet_id: str,
        smartsheet_row_id: str,
        smartsheet_modified_at: datetime | None,
    ) -> tuple[TIRRecord, str]:
        """Insert, update, or mark unchanged based on Smartsheet row metadata."""
        existing = self.get_by_smartsheet_identity(
            session,
            smartsheet_sheet_id=smartsheet_sheet_id,
            smartsheet_row_id=smartsheet_row_id,
        )
        sync_timestamp = utc_now()
        if existing is None:
            record = self.add(
                session,
                tir,
                smartsheet_sheet_id=smartsheet_sheet_id,
                smartsheet_row_id=smartsheet_row_id,
            )
            record.smartsheet_modified_at = smartsheet_modified_at
            record.last_synced_at = sync_timestamp
            return record, "created"

        if _same_modified_at(existing.smartsheet_modified_at, smartsheet_modified_at):
            existing.last_synced_at = sync_timestamp
            session.flush()
            return existing, "unchanged"

        _apply_tir_to_record(existing, tir)
        existing.smartsheet_modified_at = smartsheet_modified_at
        existing.last_synced_at = sync_timestamp
        session.flush()
        return existing, "updated"

    def get_by_smartsheet_identity(
        self,
        session: Session,
        *,
        smartsheet_sheet_id: str,
        smartsheet_row_id: str,
    ) -> TIRRecord | None:
        """Return one TIR record by Smartsheet sheet and row ID."""
        return session.scalar(
            select(TIRRecord).where(
                TIRRecord.smartsheet_sheet_id == smartsheet_sheet_id,
                TIRRecord.smartsheet_row_id == smartsheet_row_id,
            )
        )

    def get_by_registry_file_ref(
        self,
        session: Session,
        registry_file_ref: str,
    ) -> TIRRecord | None:
        """Return one TIR record by registry file reference."""
        return session.scalar(
            select(TIRRecord).where(TIRRecord.registry_file_ref == registry_file_ref)
        )

    def list_all(self, session: Session) -> list[TIRRecord]:
        """Return all TIR records."""
        return list(session.scalars(select(TIRRecord)).all())

    def get_by_id(self, session: Session, record_id: str) -> TIRRecord | None:
        """Return one TIR record by primary key."""
        return session.get(TIRRecord, record_id)

    def list_filtered(
        self,
        session: Session,
        *,
        project_status: str | None = None,
        funding_source: str | None = None,
        department_code: str | None = None,
        location: str | None = None,
        registry_file_ref: str | None = None,
        contact_email: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
    ) -> tuple[list[TIRRecord], int]:
        """Return filtered TIR records and total count."""
        stmt = select(TIRRecord)
        if project_status:
            stmt = stmt.where(TIRRecord.project_status == project_status)
        if funding_source:
            stmt = stmt.where(TIRRecord.funding_source == funding_source)
        if department_code:
            stmt = stmt.where(TIRRecord.mise_hod == department_code)
        if location:
            stmt = stmt.where(TIRRecord.project_location == location)
        if registry_file_ref:
            stmt = stmt.where(TIRRecord.registry_file_ref == registry_file_ref)
        if contact_email:
            stmt = stmt.where(TIRRecord.contact_email == contact_email)

        total = _count(session, stmt)
        stmt = _apply_sort(
            stmt,
            TIRRecord,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_fields={
                "created",
                "created_at",
                "project_name",
                "project_status",
                "funding_source",
                "mise_hod",
                "project_location",
                "registry_file_ref",
                "contact_email",
            },
        )
        records = list(session.scalars(stmt.limit(limit).offset(offset)).all())
        return records, total


class ProjectRepository:
    """Repository for discovered project folders."""

    def list_filtered(
        self,
        session: Session,
        *,
        registry_file_ref: str | None = None,
        project_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "folder_name",
        sort_order: SortOrder = "asc",
    ) -> tuple[list[ProjectFolderInventory], int]:
        """Return filtered folder inventory records and total count."""
        stmt = select(ProjectFolderInventory)
        if registry_file_ref:
            stmt = stmt.where(ProjectFolderInventory.inferred_registry_file_ref == registry_file_ref)
        if project_name:
            stmt = stmt.where(ProjectFolderInventory.inferred_project_name == project_name)

        total = _count(session, stmt)
        stmt = _apply_sort(
            stmt,
            ProjectFolderInventory,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_fields={
                "folder_name",
                "folder_path",
                "modified_time",
                "inferred_registry_file_ref",
                "inferred_project_name",
            },
        )
        records = list(session.scalars(stmt.limit(limit).offset(offset)).all())
        return records, total


class ReconciliationRepository:
    """Repository for reconciliation results."""

    def list_filtered(
        self,
        session: Session,
        *,
        registry_file_ref: str | None = None,
        project_name: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
    ) -> tuple[list[ReconciliationResult], int]:
        """Return filtered reconciliation results and total count."""
        stmt = select(ReconciliationResult)
        if registry_file_ref:
            stmt = stmt.where(ReconciliationResult.registry_file_ref == registry_file_ref)
        if project_name:
            stmt = stmt.where(ReconciliationResult.project_name == project_name)
        if category:
            stmt = stmt.where(ReconciliationResult.category == category)

        total = _count(session, stmt)
        stmt = _apply_sort(
            stmt,
            ReconciliationResult,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_fields={"created_at", "project_name", "registry_file_ref", "category"},
        )
        records = list(session.scalars(stmt.limit(limit).offset(offset)).all())
        return records, total


class ReportingRepository:
    """Repository for read-only reporting summaries."""

    def summary(self, session: Session) -> dict[str, dict[str, int]]:
        """Return summary counts for API reporting."""
        return {
            "project_status": _group_counts(session, TIRRecord.project_status),
            "funding_source": _group_counts(session, TIRRecord.funding_source),
            "department_hod": _group_counts(session, TIRRecord.mise_hod),
            "service_request": _group_counts(session, TIRRecord.service_request),
            "project_location": _group_counts(session, TIRRecord.project_location),
            "reconciliation_category": _group_counts(session, ReconciliationResult.category),
            "department_code": _group_counts(session, DepartmentReportingSnapshot.department_code),
        }


def _count(session: Session, stmt: Select[tuple[object]]) -> int:
    return session.scalar(select(func.count()).select_from(stmt.subquery())) or 0


def _apply_sort(
    stmt: Select[tuple[object]],
    model: object,
    *,
    sort_by: str,
    sort_order: SortOrder,
    allowed_fields: set[str],
) -> Select[tuple[object]]:
    field_name = sort_by if sort_by in allowed_fields else next(iter(allowed_fields))
    column = getattr(model, field_name)
    return stmt.order_by(column.desc() if sort_order == "desc" else column.asc())


def _group_counts(session: Session, column: object) -> dict[str, int]:
    rows = session.execute(select(column, func.count()).group_by(column)).all()
    return {str(value or "UNSPECIFIED"): count for value, count in rows}


def _apply_tir_to_record(record: TIRRecord, tir: TechnicalIntakeRequest) -> None:
    record.created = tir.created
    record.secretary_approval = tir.secretary_approval
    record.mise_hod = tir.mise_hod
    record.registry_confirmation = tir.registry_confirmation
    record.registry_file_ref = tir.registry_file_ref
    record.client_file_ref = tir.client_file_ref
    record.organisation = tir.organisation
    record.project_name = tir.project_name
    record.service_request = tir.service_request
    record.project_location = tir.project_location
    record.project_status = tir.project_status
    record.contact_person = tir.contact_person
    record.contact_person_position = tir.contact_person_position
    record.contact_number = tir.contact_number
    record.contact_email = tir.contact_email
    record.project_background_information = tir.project_background_information
    record.funding_source = tir.funding_source


def _same_modified_at(left: datetime | None, right: datetime | None) -> bool:
    if left is None or right is None:
        return left is right

    return _utc_naive(left) == _utc_naive(right)


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value

    return value.astimezone(UTC).replace(tzinfo=None)
