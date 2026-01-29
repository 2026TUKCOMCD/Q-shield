import uuid as uuid_lib
from sqlalchemy import String, Float, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db import Base


class Scan(Base):
    __tablename__ = "scans"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)

    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 프론트 명세: QUEUED | IN_PROGRESS | COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")

    # 프론트 명세: 0.0 ~ 1.0
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 프론트 명세: 현재 수행 중 작업 설명
    message: Mapped[str] = mapped_column(String(300), nullable=False, default="Queued")

    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    findings: Mapped[list["Finding"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    inventory: Mapped["InventorySnapshot | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    heatmap: Mapped["HeatmapSnapshot | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), nullable=False)

    # SAST/SCA/CONFIG 등
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL

    algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 결제/인증 등

    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="findings")


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), primary_key=True)

    # 프론트 요구: 0~10
    pqc_readiness_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 프론트 요구: 파이차트용
    algorithm_ratios: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # 프론트 요구: 테이블(알고리즘별 횟수 + 위치)
    inventory_table: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    scan: Mapped["Scan"] = relationship(back_populates="inventory")


class HeatmapSnapshot(Base):
    __tablename__ = "heatmap_snapshots"

    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), primary_key=True)

    # 프론트 요구: 재귀 트리 JSON
    tree: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    scan: Mapped["Scan"] = relationship(back_populates="heatmap")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.uuid", ondelete="CASCADE"), nullable=False)

    # 프론트 요구
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_effort: Mapped[str] = mapped_column(String(20), nullable=False)  # "2 M/D" 같은 문자열
    ai_recommendation: Mapped[str] = mapped_column(Text, nullable=False)       # Markdown

    # 필터링 요구 파라미터용
    algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context: Mapped[str | None] = mapped_column(String(50), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="recommendations")
