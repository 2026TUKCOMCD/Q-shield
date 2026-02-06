import uuid as uuid_lib

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class User(Base):
    __tablename__ = "users"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    identities: Mapped[list["AuthIdentity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    repositories: Mapped[list["Repository"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    scans: Mapped[list["Scan"]] = relationship(back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="github")
    repo_url: Mapped[str] = mapped_column(Text, nullable=False)
    repo_full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    external_repo_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_private: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_scanned_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="repositories")
    scans: Mapped[list["Scan"]] = relationship(back_populates="repository")


class AuthIdentity(Base):
    __tablename__ = "auth_identities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="identities")
    oauth_tokens: Mapped[list["OAuthToken"]] = relationship(back_populates="identity", cascade="all, delete-orphan")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    auth_identity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_identities.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    identity: Mapped["AuthIdentity"] = relationship(back_populates="oauth_tokens")


class Scan(Base):
    __tablename__ = "scans"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_uuid: Mapped[uuid_lib.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )
    repository_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
    )
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    message: Mapped[str] = mapped_column(String(300), nullable=False, default="Queued")
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="scans")
    repository: Mapped["Repository | None"] = relationship(back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    inventory: Mapped["InventorySnapshot | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    heatmap: Mapped["HeatmapSnapshot | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="findings")


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), primary_key=True)
    pqc_readiness_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    algorithm_ratios: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    inventory_table: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    scan: Mapped["Scan"] = relationship(back_populates="inventory")


class HeatmapSnapshot(Base):
    __tablename__ = "heatmap_snapshots"

    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), primary_key=True)
    tree: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    scan: Mapped["Scan"] = relationship(back_populates="heatmap")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), nullable=False)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_effort: Mapped[str] = mapped_column(String(20), nullable=False)
    ai_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context: Mapped[str | None] = mapped_column(String(50), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="recommendations")
