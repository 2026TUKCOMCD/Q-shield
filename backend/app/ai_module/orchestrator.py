from __future__ import annotations

import uuid as uuid_lib
from collections import Counter

from sqlalchemy.orm import Session

from app.ai_analysis_store import upsert_ai_analysis_snapshot
from app.ai_module.api_client import fetch_findings
from app.ai_module.business_impact import estimate_refactor_cost
from app.ai_module.confidence import compute_confidence_score
from app.ai_module.recommendation_engine import build_recommendations
from app.ai_module.risk_aggregation import compute_risk_metrics, deduplicate_findings, summarize_inputs
from app.ai_module.schemas import AiAnalysisResponse
from app.config import AI_ANALYSIS_VERSION, AI_RAG_CORPUS_PATH


def _compute_priority_rank(findings: list[dict], risk_score: int) -> int:
    severities = Counter(str(finding.get("severity") or "UNKNOWN") for finding in findings)
    if severities.get("CRITICAL"):
        return 1
    if risk_score >= 75:
        return 2
    if risk_score >= 50:
        return 3
    if risk_score >= 25:
        return 5
    if findings:
        return 7
    return 10


def _build_analysis_summary(findings: list[dict], inputs_summary: dict, citation_missing: bool) -> str:
    if not findings:
        return "No normalized findings were available for AI analysis."

    scanner_counts = inputs_summary.get("counts_by_scanner_type") or {}
    scanner_summary = ", ".join(
        f"{scanner}={count}" for scanner, count in sorted(scanner_counts.items()) if count
    ) or "no scanner signals"

    top_rules = inputs_summary.get("top_rules") or []
    rule_summary = ", ".join(top_rules[:3]) if top_rules else "no dominant rules"
    citation_summary = "Citations unavailable from RAG corpus." if citation_missing else "NIST citations attached."
    return f"Findings summary: {scanner_summary}. Dominant rules: {rule_summary}. {citation_summary}"


async def analyze_findings(
    findings: list[dict],
    *,
    corpus_path: str | None = None,
) -> tuple[AiAnalysisResponse, list[dict], list[str]]:
    source_count = len(findings)
    prepared_findings = deduplicate_findings(findings)
    inputs_summary = summarize_inputs(prepared_findings, source_count=source_count)
    risk_metrics = compute_risk_metrics(prepared_findings)
    refactor_cost = estimate_refactor_cost(prepared_findings)
    recommendations, citations, citation_missing, nist_references = build_recommendations(
        prepared_findings,
        corpus_path=corpus_path or AI_RAG_CORPUS_PATH,
    )
    priority_rank = _compute_priority_rank(prepared_findings, int(risk_metrics["risk_score"]))
    confidence_score = compute_confidence_score(
        findings=prepared_findings,
        inputs_summary=inputs_summary,
        citation_missing=citation_missing,
        citations_count=len(citations),
    )
    if recommendations:
        for recommendation in recommendations:
            recommendation.confidence = round(max(0.0, min(1.0, confidence_score)), 4)

    response = AiAnalysisResponse(
        risk_score=int(risk_metrics["risk_score"]),
        pqc_readiness_score=int(risk_metrics["pqc_readiness_score"]),
        severity_weighted_index=float(risk_metrics["severity_weighted_index"]),
        refactor_cost_estimate=refactor_cost,
        priority_rank=priority_rank,
        recommendations=recommendations,
        analysis_summary=_build_analysis_summary(prepared_findings, inputs_summary, citation_missing),
        confidence_score=confidence_score,
        citation_missing=citation_missing,
        inputs_summary=inputs_summary,
    )
    return response, citations, nist_references


async def compute_and_persist_ai_analysis(scan_uuid: uuid_lib.UUID, db: Session) -> AiAnalysisResponse | None:
    findings = await fetch_findings(scan_uuid, db)
    if findings is None:
        return None

    response, citations, nist_references = await analyze_findings(findings)
    upsert_ai_analysis_snapshot(
        db,
        scan_uuid,
        response,
        citations=citations,
        nist_references=nist_references,
        analysis_version=AI_ANALYSIS_VERSION,
    )
    return response
