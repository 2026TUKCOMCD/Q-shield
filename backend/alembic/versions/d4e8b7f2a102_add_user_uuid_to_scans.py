"""add user uuid to scans

Revision ID: d4e8b7f2a102
Revises: c3d9a6e7f101
Create Date: 2026-02-06 18:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e8b7f2a102"
down_revision: Union[str, Sequence[str], None] = "c3d9a6e7f101"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("user_uuid", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_scans_user_uuid_users",
        "scans",
        "users",
        ["user_uuid"],
        ["uuid"],
        ondelete="SET NULL",
    )
    op.create_index("ix_scans_user_uuid", "scans", ["user_uuid"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scans_user_uuid", table_name="scans")
    op.drop_constraint("fk_scans_user_uuid_users", "scans", type_="foreignkey")
    op.drop_column("scans", "user_uuid")
