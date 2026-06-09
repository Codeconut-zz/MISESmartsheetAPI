"""Initial persistence schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial tables."""
    def timestamp_columns() -> list[sa.Column]:
        return [
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ]

    op.create_table(
        "tir_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("smartsheet_sheet_id", sa.String(length=255), nullable=False),
        sa.Column("smartsheet_row_id", sa.String(length=255), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("secretary_approval", sa.Boolean(), nullable=False),
        sa.Column("mise_hod", sa.String(length=255), nullable=False),
        sa.Column("registry_confirmation", sa.Boolean(), nullable=False),
        sa.Column("registry_file_ref", sa.String(length=255), nullable=False),
        sa.Column("client_file_ref", sa.String(length=255), nullable=False),
        sa.Column("organisation", sa.String(length=255), nullable=False),
        sa.Column("project_name", sa.String(length=500), nullable=False),
        sa.Column("service_request", sa.Text(), nullable=False),
        sa.Column("project_location", sa.String(length=255), nullable=False),
        sa.Column("project_status", sa.String(length=50), nullable=False),
        sa.Column("contact_person", sa.String(length=255), nullable=False),
        sa.Column("contact_person_position", sa.String(length=255), nullable=False),
        sa.Column("contact_number", sa.String(length=100), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("project_background_information", sa.Text(), nullable=False),
        sa.Column("funding_source", sa.String(length=255), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_tir_records_registry_file_ref", "tir_records", ["registry_file_ref"])
    op.create_index("ix_tir_records_project_name", "tir_records", ["project_name"])
    op.create_index("ix_tir_records_contact_email", "tir_records", ["contact_email"])
    op.create_index("ix_tir_records_project_status", "tir_records", ["project_status"])
    op.create_index("ix_tir_records_funding_source", "tir_records", ["funding_source"])

    op.create_table(
        "project_folder_inventory",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("folder_path", sa.String(length=1000), nullable=False),
        sa.Column("folder_name", sa.String(length=500), nullable=False),
        sa.Column("parent_path", sa.String(length=1000), nullable=False),
        sa.Column("modified_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inferred_registry_file_ref", sa.String(length=255), nullable=True),
        sa.Column("inferred_project_name", sa.String(length=500), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_project_folder_inventory_registry_file_ref",
        "project_folder_inventory",
        ["inferred_registry_file_ref"],
    )
    op.create_index(
        "ix_project_folder_inventory_project_name",
        "project_folder_inventory",
        ["inferred_project_name"],
    )

    op.create_table(
        "reconciliation_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tir_record_id", sa.String(length=36), nullable=False),
        sa.Column("registry_file_ref", sa.String(length=255), nullable=False),
        sa.Column("project_name", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("matched_folder_path", sa.String(length=1000), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_reconciliation_results_registry_file_ref",
        "reconciliation_results",
        ["registry_file_ref"],
    )
    op.create_index(
        "ix_reconciliation_results_project_name",
        "reconciliation_results",
        ["project_name"],
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "department_reporting_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scope", sa.String(length=100), nullable=False),
        sa.Column("department_code", sa.String(length=50), nullable=False),
        sa.Column("division_code", sa.String(length=50), nullable=True),
        sa.Column("funding_source", sa.String(length=255), nullable=True),
        sa.Column("project_count", sa.Integer(), nullable=False),
        sa.Column("status_breakdown", sa.JSON(), nullable=False),
        sa.Column("funding_source_breakdown", sa.JSON(), nullable=False),
        sa.Column("data_quality_issue_count", sa.Integer(), nullable=False),
        sa.Column("missing_folder_count", sa.Integer(), nullable=False),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_department_reporting_snapshots_department_code",
        "department_reporting_snapshots",
        ["department_code"],
    )
    op.create_index(
        "ix_department_reporting_snapshots_funding_source",
        "department_reporting_snapshots",
        ["funding_source"],
    )


def downgrade() -> None:
    """Drop initial tables."""
    op.drop_table("department_reporting_snapshots")
    op.drop_table("audit_events")
    op.drop_table("reconciliation_results")
    op.drop_table("project_folder_inventory")
    op.drop_table("tir_records")
