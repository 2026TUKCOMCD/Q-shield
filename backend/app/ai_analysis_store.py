from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai_module.schemas import AiAnalysisResponse
from app.models import AiAnalysisSnapshot

logger = logging.getLogger(__name__)


def _safe_analysis_mode(value: str | None) -> str:
    if value in {"real", "fallback", "mock", "error"}:
        return value
    return "fallback"


def _extract_debug(snapshot: AiAnalysisSnapshot) -> dict:
    inputs = snapshot.inputs_summary or {}
    debug = inputs.get("debug")
    if isinstance(debug, dict):
        return debug
    return {}


def serialize_ai_analysis_snapshot(snapshot: AiAnalysisSnapshot) -> AiAnalysisResponse:
    debug = _extract_debug(snapshot)
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
        analysis_mode=_safe_analysis_mode(str(debug.get("analysis_mode") or "fallback")),
        rag_corpus_loaded=bool(debug.get("rag_corpus_loaded")),
        rag_chunks_retrieved=int(debug.get("rag_chunks_retrieved") or 0),
        citations_available=bool(debug.get("citations_available") or snapshot.citations_count),
        llm_model_used=debug.get("llm_model_used"),
        embedding_model_used=debug.get("embedding_model_used"),
        vector_store_collection=debug.get("vector_store_collection"),
        debug_message=debug.get("debug_message"),
        failure_reason=debug.get("failure_reason"),
    )


def get_ai_analysis_snapshot(db: Session, scan_uuid: uuid_lib.UUID) -> AiAnalysisSnapshot | None:
    return db.query(AiAnalysisSnapshot).filter(AiAnalysisSnapshot.scan_uuid == scan_uuid).first()


def _extract_cache_signature(snapshot: AiAnalysisSnapshot) -> str | None:
    inputs = snapshot.inputs_summary or {}
    cache_info = inputs.get("cache")
    if not isinstance(cache_info, dict):
        return None
    signature = cache_info.get("algorithm_signature")
    if isinstance(signature, str) and signature.strip():
        return signature.strip()
    return None


def find_cached_snapshot_by_algorithm_signature(
    db: Session,
    *,
    algorithm_signature: str,
    max_age_hours: int,
    analysis_version: str,
) -> AiAnalysisSnapshot | None:
    if not algorithm_signature.strip():
        return None

    threshold = datetime.now(timezone.utc) - timedelta(hours=max(1, int(max_age_hours)))
    candidates = (
        db.query(AiAnalysisSnapshot)
        .filter(AiAnalysisSnapshot.analysis_version == analysis_version)
        .filter(AiAnalysisSnapshot.citations_count > 0)
        .filter(AiAnalysisSnapshot.updated_at >= threshold)
        .order_by(AiAnalysisSnapshot.updated_at.desc())
        .limit(300)
        .all()
    )

    for snapshot in candidates:
        debug = _extract_debug(snapshot)
        if _safe_analysis_mode(str(debug.get("analysis_mode"))) != "real":
            continue
        signature = _extract_cache_signature(snapshot)
        if signature == algorithm_signature:
            return snapshot
    return None


def upsert_ai_analysis_snapshot(
    db: Session,
    scan_uuid: uuid_lib.UUID,
    payload: AiAnalysisResponse,
    *,
    citations: list[dict],
    nist_references: list[str],
    analysis_version: str,
) -> AiAnalysisSnapshot:
    logger.info("ai_analysis_store stage=upsert_start scan_uuid=%s", str(scan_uuid))
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
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "ai_analysis_store stage=upsert_failed scan_uuid=%s reason=%s",
            str(scan_uuid),
            str(exc),
        )
        raise
    db.refresh(snapshot)
    logger.info(
        "ai_analysis_store stage=upsert_done scan_uuid=%s mode=%s citations=%s",
        str(scan_uuid),
        payload.analysis_mode,
        len(citations or []),
    )
    return snapshot
