"""add username and split oauth identities

Revision ID: a7b9c2d4e601
Revises: a1f4c8b7d901
Create Date: 2026-05-05 20:40:00.000000
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7b9c2d4e601"
down_revision: Union[str, Sequence[str], None] = "a1f4c8b7d901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _username_base(email: str | None, fallback: str) -> str:
    raw = (email or fallback).split("@", 1)[0].lower()
    chars = [ch if ch.isalnum() or ch == "_" else "_" for ch in raw]
    base = "".join(chars).strip("_") or fallback
    if len(base) < 3:
        base = f"user_{base}"
    return base[:40]


def _unique_username(bind, base: str) -> str:
    username = base
    suffix = 2
    while bind.execute(
        sa.text("SELECT 1 FROM users WHERE lower(username) = lower(:username) LIMIT 1"),
        {"username": username},
    ).scalar():
        username = f"{base[:40]}_{suffix}"
        suffix += 1
    return username


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))
    op.execute("DROP INDEX IF EXISTS uq_users_email_active")

    bind = op.get_bind()

    local_rows = bind.execute(
        sa.text(
            "SELECT u.uuid, u.email, ai.id AS identity_id "
            "FROM users u "
            "JOIN auth_identities ai ON ai.user_uuid = u.uuid "
            "WHERE ai.provider = 'local' AND u.deleted_at IS NULL AND ai.deleted_at IS NULL "
            "ORDER BY u.created_at, ai.id"
        )
    ).mappings()
    for row in local_rows:
        username = _unique_username(bind, _username_base(row["email"], f"user_{str(row['uuid'])[:8]}"))
        bind.execute(
            sa.text("UPDATE users SET username = :username WHERE uuid = :uuid"),
            {"username": username, "uuid": str(row["uuid"])},
        )
        bind.execute(
            sa.text("UPDATE auth_identities SET provider_user_id = :username WHERE id = :identity_id"),
            {"username": username, "identity_id": row["identity_id"]},
        )

    op.execute(
        "CREATE UNIQUE INDEX uq_users_username_active ON users (lower(username)) "
        "WHERE username IS NOT NULL AND deleted_at IS NULL"
    )

    # Old behavior merged OAuth identities into an existing user when emails matched.
    # New behavior treats each OAuth provider account as its own service account.
    merged_social_rows = bind.execute(
        sa.text(
            "SELECT ai.id, ai.user_uuid, ai.provider, ai.provider_user_id, ai.provider_email, "
            "u.email, u.display_name, u.avatar_url, u.status, u.is_email_verified, u.last_login_at "
            "FROM auth_identities ai "
            "JOIN users u ON u.uuid = ai.user_uuid "
            "WHERE ai.provider IN ('google', 'github') "
            "AND ai.deleted_at IS NULL "
            "AND u.deleted_at IS NULL "
            "AND EXISTS ("
            "  SELECT 1 FROM auth_identities ail "
            "  WHERE ail.user_uuid = ai.user_uuid AND ail.provider = 'local' AND ail.deleted_at IS NULL"
            ") "
            "AND ("
            "  SELECT count(*) FROM auth_identities ai2 "
            "  WHERE ai2.user_uuid = ai.user_uuid AND ai2.deleted_at IS NULL"
            ") > 1 "
            "ORDER BY ai.user_uuid, ai.provider, ai.id"
        )
    ).mappings()

    for row in merged_social_rows:
        new_uuid = uuid.uuid4()
        bind.execute(
            sa.text(
                "INSERT INTO users "
                "(uuid, username, email, password_hash, display_name, avatar_url, status, "
                "is_email_verified, failed_login_count, last_login_at) "
                "VALUES (:uuid, NULL, :email, NULL, :display_name, :avatar_url, :status, "
                ":is_email_verified, 0, :last_login_at)"
            ),
            {
                "uuid": str(new_uuid),
                "email": row["provider_email"] or row["email"],
                "display_name": row["display_name"],
                "avatar_url": row["avatar_url"],
                "status": row["status"],
                "is_email_verified": row["is_email_verified"],
                "last_login_at": row["last_login_at"],
            },
        )
        bind.execute(
            sa.text("UPDATE auth_identities SET user_uuid = :user_uuid, is_primary = true WHERE id = :id"),
            {"user_uuid": str(new_uuid), "id": row["id"]},
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_username_active")
    # Do not recreate uq_users_email_active here: after this migration, separate
    # local/google/github accounts may legitimately share the same email.
    op.drop_column("users", "username")
