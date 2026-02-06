"""add repositories and link scans

Revision ID: e6f9c3a1b204
Revises: d4e8b7f2a102
Create Date: 2026-02-06 20:00:00.000000
"""

from typing import Sequence, Union
from urllib.parse import urlparse

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6f9c3a1b204"
down_revision: Union[str, Sequence[str], None] = "d4e8b7f2a102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_uuid", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="github"),
        sa.Column("repo_url", sa.Text(), nullable=False),
        sa.Column("repo_full_name", sa.String(length=300), nullable=False),
        sa.Column("external_repo_id", sa.String(length=128), nullable=True),
        sa.Column("default_branch", sa.String(length=100), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider IN ('github','google','local')", name="ck_repositories_provider"),
        sa.ForeignKeyConstraint(["user_uuid"], ["users.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repositories_user_uuid", "repositories", ["user_uuid"], unique=False)
    op.create_index("ix_repositories_repo_full_name", "repositories", ["repo_full_name"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_repositories_user_provider_full_name_active "
        "ON repositories (user_uuid, provider, repo_full_name) WHERE deleted_at IS NULL"
    )

    op.add_column("scans", sa.Column("repository_id", sa.BigInteger(), nullable=True))

    # Backfill repositories for existing user-owned scans.
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT uuid, user_uuid, github_url, created_at "
            "FROM scans "
            "WHERE user_uuid IS NOT NULL"
        )
    ).fetchall()
    repo_cache: dict[tuple[str, str], int] = {}
    for row in rows:
        scan_uuid = row[0]
        user_uuid = row[1]
        github_url = row[2] or ""
        created_at = row[3]

        parsed = urlparse(github_url)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2:
            repo = parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            repo_full_name = f"{parts[0]}/{repo}"
        else:
            repo_full_name = "unknown/unknown"
        cache_key = (str(user_uuid), repo_full_name)
        repo_id = repo_cache.get(cache_key)
        if repo_id is None:
            repo_id = bind.execute(
                sa.text(
                    "INSERT INTO repositories "
                    "(user_uuid, provider, repo_url, repo_full_name, is_active, last_scanned_at) "
                    "VALUES (:user_uuid, 'github', :repo_url, :repo_full_name, true, :last_scanned_at) "
                    "ON CONFLICT DO NOTHING "
                    "RETURNING id"
                ),
                {
                    "user_uuid": str(user_uuid),
                    "repo_url": github_url,
                    "repo_full_name": repo_full_name,
                    "last_scanned_at": created_at,
                },
            ).scalar()

            if repo_id is None:
                repo_id = bind.execute(
                    sa.text(
                        "SELECT id FROM repositories "
                        "WHERE user_uuid = :user_uuid AND provider = 'github' "
                        "AND repo_full_name = :repo_full_name AND deleted_at IS NULL "
                        "LIMIT 1"
                    ),
                    {
                        "user_uuid": str(user_uuid),
                        "repo_full_name": repo_full_name,
                    },
                ).scalar()

            repo_cache[cache_key] = int(repo_id)

        bind.execute(
            sa.text("UPDATE scans SET repository_id = :repository_id WHERE uuid = :scan_uuid"),
            {"repository_id": int(repo_id), "scan_uuid": str(scan_uuid)},
        )

    op.create_foreign_key(
        "fk_scans_repository_id_repositories",
        "scans",
        "repositories",
        ["repository_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_scans_repository_id", "scans", ["repository_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scans_repository_id", table_name="scans")
    op.drop_constraint("fk_scans_repository_id_repositories", "scans", type_="foreignkey")
    op.drop_column("scans", "repository_id")

    op.execute("DROP INDEX IF EXISTS uq_repositories_user_provider_full_name_active")
    op.drop_index("ix_repositories_repo_full_name", table_name="repositories")
    op.drop_index("ix_repositories_user_uuid", table_name="repositories")
    op.drop_table("repositories")
