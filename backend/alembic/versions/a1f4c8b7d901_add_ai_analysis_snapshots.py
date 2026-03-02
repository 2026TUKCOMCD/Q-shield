"""add ai analysis snapshots

Revision ID: a1f4c8b7d901
Revises: f1c2d3e4a501
Create Date: 2026-03-02 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1f4c8b7d901"
down_revision: Union[str, None] = "f1c2d3e4a501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_analysis_snapshots",
        sa.Column("scan_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("pqc_readiness_score", sa.Integer(), nullable=False),
        sa.Column("severity_weighted_index", sa.Float(), nullable=False),
        sa.Column("refactor_cost_level", sa.String(length=10), nullable=False),
        sa.Column("refactor_cost_explanation", sa.Text(), nullable=False),
        sa.Column("affected_files_count", sa.Integer(), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("analysis_summary", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("nist_standard_reference", sa.Text(), nullable=False),
        sa.Column("citation_missing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("citations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inputs_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("analysis_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scan_uuid"], ["scans.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("scan_uuid"),
    )


def downgrade() -> None:
    op.drop_table("ai_analysis_snapshots")
