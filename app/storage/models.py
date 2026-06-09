"""SQLAlchemy ORM models."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_uuid() -> str:
    """Return a new UUID string."""
    return str(uuid4())


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for ORM models."""


class TimestampMixin:
    """Created and updated timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class TIRRecord(Base, TimestampMixin):
    """Persisted Technical Intake Request."""

    __tablename__ = "tir_records"
    __table_args__ = (
        Index("ix_tir_records_registry_file_ref", "registry_file_ref"),
        Index("ix_tir_records_project_name", "project_name"),
        Index("ix_tir_records_contact_email", "contact_email"),
        Index("ix_tir_records_project_status", "project_status"),
        Index("ix_tir_records_funding_source", "funding_source"),
        Index("ix_tir_records_smartsheet_identity", "smartsheet_sheet_id", "smartsheet_row_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    smartsheet_sheet_id: Mapped[str] = mapped_column(String(255), default="")
    smartsheet_row_id: Mapped[str] = mapped_column(String(255), default="")
    smartsheet_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    secretary_approval: Mapped[bool] = mapped_column(Boolean)
    mise_hod: Mapped[str] = mapped_column(String(255))
    registry_confirmation: Mapped[bool] = mapped_column(Boolean)
    registry_file_ref: Mapped[str] = mapped_column(String(255))
    client_file_ref: Mapped[str] = mapped_column(String(255), default="")
    organisation: Mapped[str] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(500))
    service_request: Mapped[str] = mapped_column(Text)
    project_location: Mapped[str] = mapped_column(String(255))
    project_status: Mapped[str] = mapped_column(String(50))
    contact_person: Mapped[str] = mapped_column(String(255))
    contact_person_position: Mapped[str] = mapped_column(String(255), default="")
    contact_number: Mapped[str] = mapped_column(String(100), default="")
    contact_email: Mapped[str] = mapped_column(String(255))
    project_background_information: Mapped[str] = mapped_column(Text, default="")
    funding_source: Mapped[str] = mapped_column(String(255), default="")


class ProjectFolderInventory(Base, TimestampMixin):
    """Persisted project folder inventory row."""

    __tablename__ = "project_folder_inventory"
    __table_args__ = (
        Index("ix_project_folder_inventory_registry_file_ref", "inferred_registry_file_ref"),
        Index("ix_project_folder_inventory_project_name", "inferred_project_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    folder_path: Mapped[str] = mapped_column(String(1000))
    folder_name: Mapped[str] = mapped_column(String(500))
    parent_path: Mapped[str] = mapped_column(String(1000), default="")
    modified_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inferred_registry_file_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inferred_project_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0)


class ReconciliationResult(Base, TimestampMixin):
    """Persisted reconciliation result."""

    __tablename__ = "reconciliation_results"
    __table_args__ = (
        Index("ix_reconciliation_results_registry_file_ref", "registry_file_ref"),
        Index("ix_reconciliation_results_project_name", "project_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tir_record_id: Mapped[str] = mapped_column(String(36))
    registry_file_ref: Mapped[str] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(100))
    confidence_score: Mapped[float] = mapped_column(Float)
    matched_folder_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)


class AuditEventRecord(Base, TimestampMixin):
    """Persisted audit event."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(255))
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(255))
    environment: Mapped[str] = mapped_column(String(50))
    dry_run: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class DepartmentReportingSnapshot(Base, TimestampMixin):
    """Persisted department reporting snapshot."""

    __tablename__ = "department_reporting_snapshots"
    __table_args__ = (
        Index("ix_department_reporting_snapshots_department_code", "department_code"),
        Index("ix_department_reporting_snapshots_funding_source", "funding_source"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    scope: Mapped[str] = mapped_column(String(100))
    department_code: Mapped[str] = mapped_column(String(50))
    division_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    funding_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_count: Mapped[int] = mapped_column(Integer, default=0)
    status_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    funding_source_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_quality_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_folder_count: Mapped[int] = mapped_column(Integer, default=0)


class AttachmentMetadataRecord(Base, TimestampMixin):
    """Persisted Smartsheet attachment metadata without file contents."""

    __tablename__ = "attachment_metadata"
    __table_args__ = (
        Index("ix_attachment_metadata_attachment_id", "attachment_id", unique=True),
        Index("ix_attachment_metadata_tir_record_id", "tir_record_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    attachment_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(500))
    size: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(255), default="")
    source_url: Mapped[str] = mapped_column(String(2000), default="")
    tir_record_id: Mapped[str] = mapped_column(String(36), default="")
    smartsheet_sheet_id: Mapped[str] = mapped_column(String(255), default="")
    smartsheet_row_id: Mapped[str] = mapped_column(String(255), default="")
    sanitized_filename: Mapped[str] = mapped_column(String(500), default="")


class WebhookEventRecord(Base, TimestampMixin):
    """Persisted inbound webhook event queued for background processing."""

    __tablename__ = "webhook_events"
    __table_args__ = (Index("ix_webhook_events_event_id", "event_id", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100), default="smartsheet")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
