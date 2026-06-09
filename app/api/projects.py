"""Project folder read API router."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api.schemas import PaginationMeta, ProjectListResponse, ProjectRead
from app.storage.repositories import ProjectRepository

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
def list_projects(
    registry_file_ref: str | None = None,
    project_name: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = "folder_name",
    sort_order: Literal["asc", "desc"] = "asc",
    session: Session = Depends(get_db_session),
) -> ProjectListResponse:
    """List discovered project folders."""
    records, total = ProjectRepository().list_filtered(
        session,
        registry_file_ref=registry_file_ref,
        project_name=project_name,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ProjectListResponse(
        items=[ProjectRead.model_validate(record) for record in records],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )
