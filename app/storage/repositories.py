"""Repository layer for persisted application records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.tir import TechnicalIntakeRequest
from app.storage.models import TIRRecord


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
