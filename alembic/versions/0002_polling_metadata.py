"""Add TIR polling metadata.

Revision ID: 0002_polling_metadata
Revises: 0001_initial
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_polling_metadata"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add polling metadata columns."""
    op.add_column(
        "tir_records",
        sa.Column("smartsheet_modified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tir_records",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tir_records_smartsheet_identity",
        "tir_records",
        ["smartsheet_sheet_id", "smartsheet_row_id"],
    )


def downgrade() -> None:
    """Remove polling metadata columns."""
    op.drop_index("ix_tir_records_smartsheet_identity", table_name="tir_records")
    op.drop_column("tir_records", "last_synced_at")
    op.drop_column("tir_records", "smartsheet_modified_at")
