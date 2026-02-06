"""add users and auth tables

Revision ID: c3d9a6e7f101
Revises: b853473cd69b
Create Date: 2026-02-06 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d9a6e7f101"
down_revision: Union[str, Sequence[str], None] = "b853473cd69b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','PENDING','DELETED')", name="ck_users_status"),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("ix_users_status", "users", ["status"], unique=False)
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_users_email_active ON users (lower(email)) "
        "WHERE email IS NOT NULL AND deleted_at IS NULL"
    )

    op.create_table(
        "auth_identities",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_uuid", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=True),
        sa.Column("provider_email", sa.String(length=320), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider IN ('local','github','google')", name="ck_auth_identities_provider"),
        sa.ForeignKeyConstraint(["user_uuid"], ["users.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_identities_user_uuid", "auth_identities", ["user_uuid"], unique=False)
    op.create_index("ix_auth_identities_provider", "auth_identities", ["provider"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_auth_identities_provider_account_active "
        "ON auth_identities (provider, provider_user_id) "
        "WHERE provider_user_id IS NOT NULL AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_auth_identities_user_provider_active "
        "ON auth_identities (user_uuid, provider) WHERE deleted_at IS NULL"
    )

    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("auth_identity_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=30), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("provider IN ('github','google')", name="ck_oauth_tokens_provider"),
        sa.ForeignKeyConstraint(["auth_identity_id"], ["auth_identities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oauth_tokens_identity_provider", "oauth_tokens", ["auth_identity_id", "provider"], unique=False)
    op.create_index("ix_oauth_tokens_expires_at", "oauth_tokens", ["expires_at"], unique=False)
    op.create_index("ix_oauth_tokens_revoked_at", "oauth_tokens", ["revoked_at"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_oauth_tokens_active_identity_provider "
        "ON oauth_tokens (auth_identity_id, provider) WHERE revoked_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_oauth_tokens_active_identity_provider")
    op.drop_index("ix_oauth_tokens_revoked_at", table_name="oauth_tokens")
    op.drop_index("ix_oauth_tokens_expires_at", table_name="oauth_tokens")
    op.drop_index("ix_oauth_tokens_identity_provider", table_name="oauth_tokens")
    op.drop_table("oauth_tokens")

    op.execute("DROP INDEX IF EXISTS uq_auth_identities_user_provider_active")
    op.execute("DROP INDEX IF EXISTS uq_auth_identities_provider_account_active")
    op.drop_index("ix_auth_identities_provider", table_name="auth_identities")
    op.drop_index("ix_auth_identities_user_uuid", table_name="auth_identities")
    op.drop_table("auth_identities")

    op.execute("DROP INDEX IF EXISTS uq_users_email_active")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
