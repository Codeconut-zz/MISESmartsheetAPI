"""TIR read API router."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api.schemas import TIRListResponse, TIRRecordRead, PaginationMeta
from app.storage.repositories import TIRRecordRepository

router = APIRouter(prefix="/api/v1/tir", tags=["tir"])


@router.get("", response_model=TIRListResponse)
def list_tir_records(
    project_status: str | None = None,
    funding_source: str | None = None,
    department_code: str | None = None,
    location: str | None = None,
    registry_file_ref: str | None = None,
    contact_email: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    session: Session = Depends(get_db_session),
) -> TIRListResponse:
    """List TIR records with filters, pagination, and sorting."""
    records, total = TIRRecordRepository().list_filtered(
        session,
        project_status=project_status,
        funding_source=funding_source,
        department_code=department_code,
        location=location,
        registry_file_ref=registry_file_ref,
        contact_email=contact_email,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TIRListResponse(
        items=[TIRRecordRead.model_validate(record) for record in records],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )


@router.get("/{record_id}", response_model=TIRRecordRead)
def get_tir_record(
    record_id: str,
    session: Session = Depends(get_db_session),
) -> TIRRecordRead:
    """Return one TIR record by ID."""
    record = TIRRecordRepository().get_by_id(session, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="TIR record not found")

    return TIRRecordRead.model_validate(record)
