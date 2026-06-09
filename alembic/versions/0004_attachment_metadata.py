"""Add attachment metadata table.

Revision ID: 0004_attachment_metadata
Revises: 0003_webhook_events
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_attachment_metadata"
down_revision: str | None = "0003_webhook_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create attachment metadata table."""
    op.create_table(
        "attachment_metadata",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attachment_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=2000), nullable=False),
        sa.Column("tir_record_id", sa.String(length=36), nullable=False),
        sa.Column("smartsheet_sheet_id", sa.String(length=255), nullable=False),
        sa.Column("smartsheet_row_id", sa.String(length=255), nullable=False),
        sa.Column("sanitized_filename", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_attachment_metadata_attachment_id",
        "attachment_metadata",
        ["attachment_id"],
        unique=True,
    )
    op.create_index(
        "ix_attachment_metadata_tir_record_id",
        "attachment_metadata",
        ["tir_record_id"],
    )


def downgrade() -> None:
    """Drop attachment metadata table."""
    op.drop_index("ix_attachment_metadata_tir_record_id", table_name="attachment_metadata")
    op.drop_index("ix_attachment_metadata_attachment_id", table_name="attachment_metadata")
    op.drop_table("attachment_metadata")
