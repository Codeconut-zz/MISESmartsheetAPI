"""Reconciliation read API router."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api.schemas import PaginationMeta, ReconciliationListResponse, ReconciliationRead
from app.storage.repositories import ReconciliationRepository

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.get("", response_model=ReconciliationListResponse)
def list_reconciliation_results(
    registry_file_ref: str | None = None,
    project_name: str | None = None,
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    session: Session = Depends(get_db_session),
) -> ReconciliationListResponse:
    """List reconciliation results."""
    records, total = ReconciliationRepository().list_filtered(
        session,
        registry_file_ref=registry_file_ref,
        project_name=project_name,
        category=category,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ReconciliationListResponse(
        items=[ReconciliationRead.model_validate(record) for record in records],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )
