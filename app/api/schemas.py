"""API response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    total: int


class TIRRecordRead(BaseModel):
    """TIR record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    smartsheet_sheet_id: str
    smartsheet_row_id: str
    created: datetime
    secretary_approval: bool
    mise_hod: str
    registry_confirmation: bool
    registry_file_ref: str
    client_file_ref: str
    organisation: str
    project_name: str
    service_request: str
    project_location: str
    project_status: str
    contact_person: str
    contact_person_position: str
    contact_number: str
    contact_email: str
    project_background_information: str
    funding_source: str
    created_at: datetime
    updated_at: datetime


class TIRListResponse(BaseModel):
    """Paginated TIR response."""

    items: list[TIRRecordRead]
    meta: PaginationMeta


class ProjectRead(BaseModel):
    """Project folder inventory response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    folder_path: str
    folder_name: str
    parent_path: str
    modified_time: datetime | None
    inferred_registry_file_ref: str | None
    inferred_project_name: str | None
    file_count: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated project response."""

    items: list[ProjectRead]
    meta: PaginationMeta


class ReconciliationRead(BaseModel):
    """Reconciliation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tir_record_id: str
    registry_file_ref: str
    project_name: str
    category: str
    confidence_score: float
    matched_folder_path: str | None
    reasons: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReconciliationListResponse(BaseModel):
    """Paginated reconciliation response."""

    items: list[ReconciliationRead]
    meta: PaginationMeta


class ReportSummaryResponse(BaseModel):
    """Report summary response."""

    summary: dict[str, dict[str, int]]
