"""Add reporting snapshot metrics.

Revision ID: 0005_reporting_snapshot_metrics
Revises: 0004_attachment_metadata
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_reporting_snapshot_metrics"
down_revision: str | None = "0004_attachment_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add detailed snapshot metric columns."""
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("snapshot_name", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("pending_approvals", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("approved_projects", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("declined_projects", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("missing_data_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "department_reporting_snapshots",
        sa.Column("service_request_breakdown", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    """Remove detailed snapshot metric columns."""
    op.drop_column("department_reporting_snapshots", "service_request_breakdown")
    op.drop_column("department_reporting_snapshots", "missing_data_count")
    op.drop_column("department_reporting_snapshots", "declined_projects")
    op.drop_column("department_reporting_snapshots", "approved_projects")
    op.drop_column("department_reporting_snapshots", "pending_approvals")
    op.drop_column("department_reporting_snapshots", "snapshot_name")
