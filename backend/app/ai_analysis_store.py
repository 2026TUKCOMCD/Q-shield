from __future__ import annotations

import uuid as uuid_lib

from sqlalchemy.orm import Session

from app.ai_module.schemas import AiAnalysisResponse
from app.models import AiAnalysisSnapshot


def serialize_ai_analysis_snapshot(snapshot: AiAnalysisSnapshot) -> AiAnalysisResponse:
    return AiAnalysisResponse(
        risk_score=int(snapshot.risk_score),
        pqc_readiness_score=int(snapshot.pqc_readiness_score),
        severity_weighted_index=float(snapshot.severity_weighted_index or 0.0),
        refactor_cost_estimate={
            "level": snapshot.refactor_cost_level,
            "explanation": snapshot.refactor_cost_explanation,
            "affected_files": int(snapshot.affected_files_count or 0),
        },
        priority_rank=int(snapshot.priority_rank),
        recommendations=snapshot.recommendations or [],
        analysis_summary=snapshot.analysis_summary,
        confidence_score=float(snapshot.confidence_score or 0.0),
        citation_missing=bool(snapshot.citation_missing),
        inputs_summary=snapshot.inputs_summary or {},
    )


def get_ai_analysis_snapshot(db: Session, scan_uuid: uuid_lib.UUID) -> AiAnalysisSnapshot | None:
    return db.query(AiAnalysisSnapshot).filter(AiAnalysisSnapshot.scan_uuid == scan_uuid).first()


def upsert_ai_analysis_snapshot(
    db: Session,
    scan_uuid: uuid_lib.UUID,
    payload: AiAnalysisResponse,
    *,
    citations: list[dict],
    nist_references: list[str],
    analysis_version: str,
) -> AiAnalysisSnapshot:
    snapshot = get_ai_analysis_snapshot(db, scan_uuid)
    if snapshot is None:
        snapshot = AiAnalysisSnapshot(scan_uuid=scan_uuid)

    snapshot.risk_score = int(payload.risk_score)
    snapshot.pqc_readiness_score = int(payload.pqc_readiness_score)
    snapshot.severity_weighted_index = float(payload.severity_weighted_index)
    snapshot.refactor_cost_level = payload.refactor_cost_estimate.level
    snapshot.refactor_cost_explanation = payload.refactor_cost_estimate.explanation
    snapshot.affected_files_count = int(payload.refactor_cost_estimate.affected_files)
    snapshot.priority_rank = int(payload.priority_rank)
    snapshot.recommendations = [recommendation.model_dump() for recommendation in payload.recommendations]
    snapshot.analysis_summary = payload.analysis_summary
    snapshot.confidence_score = float(payload.confidence_score)
    snapshot.citations = citations or []
    snapshot.nist_standard_reference = ", ".join(nist_references) if nist_references else "N/A"
    snapshot.citation_missing = bool(payload.citation_missing)
    snapshot.citations_count = len(citations or [])
    snapshot.inputs_summary = payload.inputs_summary or {}
    snapshot.analysis_version = analysis_version

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
