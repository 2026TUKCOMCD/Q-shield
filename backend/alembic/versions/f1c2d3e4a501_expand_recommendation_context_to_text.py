"""expand recommendation context to text

Revision ID: f1c2d3e4a501
Revises: e6f9c3a1b204
Create Date: 2026-02-11 22:50:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4a501"
down_revision: Union[str, Sequence[str], None] = "e6f9c3a1b204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "recommendations",
        "context",
        existing_type=sa.String(length=50),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "recommendations",
        "context",
        existing_type=sa.Text(),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
