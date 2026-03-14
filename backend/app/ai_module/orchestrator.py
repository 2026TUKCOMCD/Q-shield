from __future__ import annotations

import json
import logging
import uuid as uuid_lib
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.ai_analysis_store import (
    find_cached_snapshot_by_algorithm_signature,
    serialize_ai_analysis_snapshot,
    upsert_ai_analysis_snapshot,
)
from app.ai_module.api_client import fetch_findings
from app.ai_module.business_impact import estimate_refactor_cost
from app.ai_module.confidence import compute_confidence_score
from app.ai_module.llm.openai_client import generate_grounded_ai_analysis
from app.ai_module.recommendation_engine import build_recommendations
from app.ai_module.rag.ingest import ingest_corpus
from app.ai_module.rag.retriever import inspect_rag_corpus, retrieve_relevant_chunks_with_debug
from app.ai_module.risk_aggregation import compute_risk_metrics, deduplicate_findings, summarize_inputs
from app.ai_module.schemas import AiAnalysisResponse
from app.config import (
    AI_ALLOW_DETERMINISTIC_FALLBACK,
    AI_ANALYSIS_VERSION,
    AI_AUTO_INGEST_ON_EMPTY_VECTOR,
    AI_CACHE_ENABLED,
    AI_CACHE_MAX_AGE_HOURS,
    AI_RAG_CORPUS_PATH,
    AI_RAG_TOP_K,
    AI_VECTOR_COLLECTION,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def _select_affected_locations(findings: list[dict], recommendation_text: str, max_locations: int = 3) -> list[dict]:
    text = recommendation_text.lower()
    ranked: list[tuple[int, dict]] = []
    for finding in findings:
        file_path = finding.get("file_path")
        if not file_path:
            continue
        score = 0
        algorithm = str(finding.get("algorithm") or "").lower()
        if algorithm and algorithm in text:
            score += 3
        rule_id = str((finding.get("meta") or {}).get("rule_id") or "").lower()
        finding_type = str(finding.get("type") or "").lower()
        if rule_id and rule_id in text:
            score += 2
        if finding_type and finding_type in text:
            score += 1
        severity = str(finding.get("severity") or "").upper()
        if severity == "CRITICAL":
            score += 2
        elif severity == "HIGH":
            score += 1
        if score <= 0:
            continue
        ranked.append((score, finding))

    ranked.sort(key=lambda item: item[0], reverse=True)
    locations: list[dict] = []
    seen_keys: set[tuple[str, Any, Any]] = set()
    for _, finding in ranked:
        key = (str(finding.get("file_path")), finding.get("line_start"), finding.get("line_end"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        evidence = str(finding.get("evidence") or "").strip()
        if len(evidence) > 280:
            evidence = f"{evidence[:280]}..."
        meta = finding.get("meta") or {}
        locations.append(
            {
                "file_path": str(finding.get("file_path")),
                "line_start": finding.get("line_start"),
                "line_end": finding.get("line_end"),
                "rule_id": meta.get("rule_id"),
                "scanner_type": meta.get("scanner_type"),
                "evidence_excerpt": evidence or None,
            }
        )
        if len(locations) >= max_locations:
            break
    if locations:
        return locations

    # Fallback: choose high-severity findings even if text matching is weak.
    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    fallback_candidates = [
        finding for finding in findings if finding.get("file_path")
    ]
    fallback_candidates.sort(
        key=lambda item: (
            severity_rank.get(str(item.get("severity") or "").upper(), -1),
            int(item.get("line_start") or 0),
        ),
        reverse=True,
    )
    for finding in fallback_candidates:
        key = (str(finding.get("file_path")), finding.get("line_start"), finding.get("line_end"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        evidence = str(finding.get("evidence") or "").strip()
        if len(evidence) > 280:
            evidence = f"{evidence[:280]}..."
        meta = finding.get("meta") or {}
        locations.append(
            {
                "file_path": str(finding.get("file_path")),
                "line_start": finding.get("line_start"),
                "line_end": finding.get("line_end"),
                "rule_id": meta.get("rule_id"),
                "scanner_type": meta.get("scanner_type"),
                "evidence_excerpt": evidence or None,
            }
        )
        if len(locations) >= max_locations:
            break
    return locations


def _guess_language(file_path: str | None) -> str:
    path = str(file_path or "").lower()
    if path.endswith(".py"):
        return "python"
    if path.endswith(".js"):
        return "javascript"
    if path.endswith(".ts"):
        return "typescript"
    if path.endswith(".java"):
        return "java"
    if path.endswith(".go"):
        return "go"
    if path.endswith(".c") or path.endswith(".h"):
        return "c"
    if path.endswith(".cpp") or path.endswith(".cc") or path.endswith(".hpp"):
        return "cpp"
    return "unknown"


def _fallback_fix_example(recommendation_text: str, location: dict[str, Any] | None) -> dict[str, Any] | None:
    if not location:
        return None
    file_path = str(location.get("file_path") or "")
    if not file_path:
        return None

    recommendation_lower = recommendation_text.lower()
    evidence = str(location.get("evidence_excerpt") or "").strip()
    before_code = evidence or "# legacy cryptographic usage"
    language = _guess_language(file_path)

    if "rsa" in recommendation_lower and language == "python":
        after_code = (
            "from oqs import KeyEncapsulation\n\n"
            "# Replace RSA-based key establishment with ML-KEM\n"
            "kem = KeyEncapsulation('ML-KEM-768')\n"
            "public_key = kem.generate_keypair()\n"
            "ciphertext, shared_secret = kem.encap_secret(public_key)\n"
        )
        rationale = "Replace RSA key establishment path with ML-KEM-768 KEM flow."
    elif "ecdsa" in recommendation_lower or "ecc" in recommendation_lower:
        after_code = (
            "# Replace ECDSA signing with ML-DSA compatible implementation\n"
            "# Example placeholder:\n"
            "signer = MlDsaSigner('ML-DSA-65')\n"
            "signature = signer.sign(message)\n"
        )
        rationale = "Migrate legacy signature path to ML-DSA compatible signing flow."
    elif "sha-1" in recommendation_lower or "weak hash" in recommendation_lower or "hash" in recommendation_lower:
        after_code = (
            "# Replace weak hash with SHA-256/SHA3\n"
            "import hashlib\n"
            "digest = hashlib.sha256(data).digest()\n"
        )
        rationale = "Remove weak hash usage and adopt modern hash function."
    else:
        after_code = (
            "# Replace legacy cryptographic primitive with PQC-capable implementation\n"
            "# Keep this change behind a feature flag and validate interoperability.\n"
        )
        rationale = "Use a PQC-capable primitive and phase rollout with compatibility checks."

    return {
        "file_path": file_path,
        "language": language,
        "rationale": rationale,
        "before_code": before_code,
        "after_code": after_code,
        "confidence": 0.45,
    }


def _enrich_recommendations_for_code_fix(
    response: AiAnalysisResponse,
    findings: list[dict],
) -> AiAnalysisResponse:
    updated_recommendations = []
    for recommendation in response.recommendations:
        recommendation_text = f"{recommendation.title} {recommendation.description}"
        code_fix_examples = list(recommendation.code_fix_examples or [])

        affected_locations = recommendation.affected_locations
        if not affected_locations:
            selected = _select_affected_locations(findings, recommendation_text, max_locations=3)
            affected_locations = selected

        primary_location = affected_locations[0] if affected_locations else None
        if not code_fix_examples:
            generated_fix = _fallback_fix_example(recommendation_text, primary_location)
            if generated_fix:
                code_fix_examples = [generated_fix]

        updated_recommendations.append(
            recommendation.model_copy(
                update={
                    "affected_locations": affected_locations,
                    "code_fix_examples": code_fix_examples,
                }
            )
        )

    return response.model_copy(update={"recommendations": updated_recommendations})


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


def build_rag_query(findings: list[dict]) -> str:
    reduced: list[dict] = []
    for finding in findings[:30]:
        reduced.append(
            {
                "type": finding.get("type"),
                "severity": finding.get("severity"),
                "algorithm": finding.get("algorithm"),
                "context": finding.get("context"),
                "file_path": finding.get("file_path"),
                "meta": finding.get("meta"),
            }
        )
    return (
        "Find the most relevant NIST guidance for PQC migration, cryptographic transition, "
        "TLS, IPsec, key establishment, digital signatures, and key management "
        f"for these findings:\n{json.dumps(reduced, ensure_ascii=False)}"
    )


def build_algorithm_signature(findings: list[dict]) -> str:
    algorithms: set[str] = set()
    for finding in findings:
        algorithm = str(finding.get("algorithm") or "").strip().upper()
        if algorithm:
            algorithms.add(algorithm)
            continue
        meta = finding.get("meta") or {}
        library = str(meta.get("library") or "").strip().upper()
        if library:
            algorithms.add(f"LIB:{library}")
    if not algorithms:
        return "NO_ALGORITHM_SIGNAL"
    return "|".join(sorted(algorithms))


def _build_debug_payload(
    *,
    analysis_mode: str,
    rag_corpus_loaded: bool,
    rag_chunks_retrieved: int,
    citations_available: bool,
    llm_model_used: str | None,
    embedding_model_used: str | None,
    vector_store_collection: str | None,
    debug_message: str | None = None,
    failure_reason: str | None = None,
    rag_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "analysis_mode": analysis_mode,
        "rag_corpus_loaded": rag_corpus_loaded,
        "rag_chunks_retrieved": rag_chunks_retrieved,
        "citations_available": citations_available,
        "llm_model_used": llm_model_used,
        "embedding_model_used": embedding_model_used,
        "vector_store_collection": vector_store_collection,
        "debug_message": debug_message,
        "failure_reason": failure_reason,
        "rag_details": rag_details or {},
    }


def _apply_debug_to_response(response: AiAnalysisResponse, debug_payload: dict[str, Any]) -> AiAnalysisResponse:
    next_inputs_summary = dict(response.inputs_summary or {})
    next_inputs_summary["debug"] = debug_payload
    return response.model_copy(
        update={
            "inputs_summary": next_inputs_summary,
            "analysis_mode": debug_payload.get("analysis_mode"),
            "rag_corpus_loaded": bool(debug_payload.get("rag_corpus_loaded")),
            "rag_chunks_retrieved": int(debug_payload.get("rag_chunks_retrieved") or 0),
            "citations_available": bool(debug_payload.get("citations_available")),
            "llm_model_used": debug_payload.get("llm_model_used"),
            "embedding_model_used": debug_payload.get("embedding_model_used"),
            "vector_store_collection": debug_payload.get("vector_store_collection"),
            "debug_message": debug_payload.get("debug_message"),
            "failure_reason": debug_payload.get("failure_reason"),
        }
    )


def _apply_cache_metadata(
    response: AiAnalysisResponse,
    *,
    algorithm_signature: str,
    cache_hit: bool,
    cache_source_scan: str | None = None,
) -> AiAnalysisResponse:
    next_inputs_summary = dict(response.inputs_summary or {})
    cache_payload: dict[str, Any] = {
        "algorithm_signature": algorithm_signature,
        "cache_hit": cache_hit,
    }
    if cache_source_scan:
        cache_payload["cache_source_scan"] = cache_source_scan
    next_inputs_summary["cache"] = cache_payload
    return response.model_copy(update={"inputs_summary": next_inputs_summary})


def _normalize_payload_for_storage(payload: AiAnalysisResponse) -> tuple[list[dict], list[str], bool]:
    citations: list[dict] = []
    nist_refs: list[str] = []

    for recommendation in payload.recommendations:
        if recommendation.nist_standard_reference:
            nist_refs.append(recommendation.nist_standard_reference)
        for citation in recommendation.citations:
            citations.append(citation.model_dump())

    deduped_refs = [reference for reference in dict.fromkeys(nist_refs) if reference]
    citation_missing = bool(payload.citation_missing or not citations)
    if not deduped_refs:
        deduped_refs = ["N/A"]
    return citations, deduped_refs, citation_missing


def _error_analysis(
    *,
    findings: list[dict],
    inputs_summary: dict,
    risk_metrics: dict[str, int | float],
    refactor_cost,
    priority_rank: int,
    failure_reason: str,
    rag_debug: dict[str, Any],
    algorithm_signature: str,
) -> tuple[AiAnalysisResponse, list[dict], list[str]]:
    logger.error("ai_analysis stage=error failure_reason=%s", failure_reason)
    response = AiAnalysisResponse(
        risk_score=int(risk_metrics["risk_score"]),
        pqc_readiness_score=int(risk_metrics["pqc_readiness_score"]),
        severity_weighted_index=float(risk_metrics["severity_weighted_index"]),
        refactor_cost_estimate=refactor_cost,
        priority_rank=priority_rank,
        recommendations=[],
        analysis_summary=f"AI analysis failed: {failure_reason}",
        confidence_score=0.0,
        citation_missing=True,
        inputs_summary=inputs_summary,
    )
    debug_payload = _build_debug_payload(
        analysis_mode="error",
        rag_corpus_loaded=bool(rag_debug.get("rag_corpus_loaded")),
        rag_chunks_retrieved=int(rag_debug.get("rag_chunks_retrieved") or 0),
        citations_available=False,
        llm_model_used=OPENAI_MODEL,
        embedding_model_used=OPENAI_EMBEDDING_MODEL,
        vector_store_collection=rag_debug.get("vector_store_collection") or AI_VECTOR_COLLECTION,
        debug_message="Real RAG + LLM path failed",
        failure_reason=failure_reason,
        rag_details=rag_debug,
    )
    response = _apply_debug_to_response(response, debug_payload)
    response = _apply_cache_metadata(response, algorithm_signature=algorithm_signature, cache_hit=False)
    return response, [], ["N/A"]


def _fallback_analysis(
    *,
    findings: list[dict],
    inputs_summary: dict,
    risk_metrics: dict[str, int | float],
    refactor_cost,
    priority_rank: int,
    corpus_path: str | None,
    failure_reason: str,
    rag_debug: dict[str, Any],
    algorithm_signature: str,
) -> tuple[AiAnalysisResponse, list[dict], list[str]]:
    logger.warning("ai_analysis stage=fallback reason=%s", failure_reason)
    recommendations, citations, citation_missing, nist_references = build_recommendations(
        findings,
        corpus_path=corpus_path or AI_RAG_CORPUS_PATH,
    )
    confidence_score = compute_confidence_score(
        findings=findings,
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
        analysis_summary=_build_analysis_summary(findings, inputs_summary, citation_missing),
        confidence_score=confidence_score,
        citation_missing=citation_missing,
        inputs_summary=inputs_summary,
    )

    debug_payload = _build_debug_payload(
        analysis_mode="fallback",
        rag_corpus_loaded=bool(rag_debug.get("rag_corpus_loaded")),
        rag_chunks_retrieved=int(rag_debug.get("rag_chunks_retrieved") or 0),
        citations_available=bool(citations),
        llm_model_used=OPENAI_MODEL,
        embedding_model_used=OPENAI_EMBEDDING_MODEL,
        vector_store_collection=rag_debug.get("vector_store_collection") or AI_VECTOR_COLLECTION,
        debug_message="Deterministic fallback used",
        failure_reason=failure_reason,
        rag_details=rag_debug,
    )
    response = _apply_debug_to_response(response, debug_payload)
    response = _apply_cache_metadata(response, algorithm_signature=algorithm_signature, cache_hit=False)

    if not nist_references:
        nist_references = ["N/A"]
    return response, citations, nist_references


def _maybe_auto_ingest(corpus_path: str | None, rag_debug: dict[str, Any]) -> dict[str, Any]:
    if not AI_AUTO_INGEST_ON_EMPTY_VECTOR:
        return rag_debug
    if not rag_debug.get("rag_corpus_loaded"):
        return rag_debug
    if int(rag_debug.get("vector_count") or 0) > 0:
        return rag_debug

    logger.info("ai_analysis stage=auto_ingest_start corpus_path=%s", rag_debug.get("corpus_path"))
    ingested_chunks = ingest_corpus(corpus_path=corpus_path)
    logger.info("ai_analysis stage=auto_ingest_done ingested_chunks=%s", ingested_chunks)

    refreshed = inspect_rag_corpus(corpus_path).to_dict()
    refreshed["auto_ingested_chunks"] = ingested_chunks
    return refreshed


def _ensure_real_rag_ready(
    *,
    findings: list[dict],
    inputs_summary: dict,
    risk_metrics: dict[str, int | float],
    refactor_cost,
    priority_rank: int,
    corpus_path: str | None,
    rag_debug: dict[str, Any],
    failure_reason: str,
    algorithm_signature: str,
) -> tuple[AiAnalysisResponse, list[dict], list[str]]:
    if AI_ALLOW_DETERMINISTIC_FALLBACK:
        logger.warning(
            "ai_analysis fallback_requested_but_disabled failure_reason=%s",
            failure_reason,
        )
    return _error_analysis(
        findings=findings,
        inputs_summary=inputs_summary,
        risk_metrics=risk_metrics,
        refactor_cost=refactor_cost,
        priority_rank=priority_rank,
        failure_reason=failure_reason,
        rag_debug=rag_debug,
        algorithm_signature=algorithm_signature,
    )


async def analyze_findings(
    findings: list[dict],
    *,
    corpus_path: str | None = None,
    algorithm_signature: str | None = None,
) -> tuple[AiAnalysisResponse, list[dict], list[str]]:
    source_count = len(findings)
    prepared_findings = deduplicate_findings(findings)
    inputs_summary = summarize_inputs(prepared_findings, source_count=source_count)
    risk_metrics = compute_risk_metrics(prepared_findings)
    refactor_cost = estimate_refactor_cost(prepared_findings)
    priority_rank = _compute_priority_rank(prepared_findings, int(risk_metrics["risk_score"]))
    effective_signature = algorithm_signature or build_algorithm_signature(prepared_findings)

    logger.info(
        "ai_analysis stage=start findings_source=%s findings_deduped=%s fallback_enabled=%s",
        source_count,
        len(prepared_findings),
        AI_ALLOW_DETERMINISTIC_FALLBACK,
    )

    rag_status = inspect_rag_corpus(corpus_path)
    rag_debug = _maybe_auto_ingest(corpus_path, rag_status.to_dict())

    if not rag_debug.get("rag_corpus_loaded"):
        failure_reason = rag_debug.get("failure_reason") or "RAG corpus is not loaded"
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason=failure_reason,
            algorithm_signature=effective_signature,
        )

    if not rag_debug.get("vector_store_ready"):
        failure_reason = rag_debug.get("failure_reason") or "Vector store is unavailable"
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason=failure_reason,
            algorithm_signature=effective_signature,
        )

    if int(rag_debug.get("vector_count") or 0) <= 0:
        failure_reason = "Vector store is empty. Run corpus ingest before AI analysis."
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason=failure_reason,
            algorithm_signature=effective_signature,
        )

    rag_query = build_rag_query(prepared_findings)
    retrieval_result = retrieve_relevant_chunks_with_debug(rag_query, top_k=AI_RAG_TOP_K)
    rag_debug["rag_chunks_retrieved"] = len(retrieval_result.chunks)
    rag_debug["vector_store_collection"] = retrieval_result.vector_store_collection or rag_debug.get(
        "vector_store_collection"
    )

    if retrieval_result.failure_reason:
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason=retrieval_result.failure_reason,
            algorithm_signature=effective_signature,
        )

    if not retrieval_result.chunks:
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason="No relevant chunks were retrieved for the findings query",
            algorithm_signature=effective_signature,
        )

    try:
        llm_payload = generate_grounded_ai_analysis(
            findings=prepared_findings,
            retrieved_chunks=retrieval_result.chunks,
            risk_metrics=risk_metrics,
            refactor_cost_estimate=refactor_cost.model_dump(),
            priority_rank=priority_rank,
            inputs_summary=inputs_summary,
        )
        response = AiAnalysisResponse.model_validate(llm_payload)
        response = _enrich_recommendations_for_code_fix(response, prepared_findings)
    except Exception as exc:
        return _ensure_real_rag_ready(
            findings=prepared_findings,
            inputs_summary=inputs_summary,
            risk_metrics=risk_metrics,
            refactor_cost=refactor_cost,
            priority_rank=priority_rank,
            corpus_path=corpus_path,
            rag_debug=rag_debug,
            failure_reason=f"LLM generation failed: {exc}",
            algorithm_signature=effective_signature,
        )

    citations, nist_references, citation_missing = _normalize_payload_for_storage(response)
    confidence_score = compute_confidence_score(
        findings=prepared_findings,
        inputs_summary=inputs_summary,
        citation_missing=citation_missing,
        citations_count=len(citations),
    )

    response = response.model_copy(
        update={
            "analysis_summary": response.analysis_summary
            or _build_analysis_summary(prepared_findings, inputs_summary, citation_missing),
            "confidence_score": confidence_score,
            "citation_missing": citation_missing,
            "inputs_summary": inputs_summary,
        }
    )
    debug_payload = _build_debug_payload(
        analysis_mode="real",
        rag_corpus_loaded=True,
        rag_chunks_retrieved=len(retrieval_result.chunks),
        citations_available=bool(citations),
        llm_model_used=OPENAI_MODEL,
        embedding_model_used=OPENAI_EMBEDDING_MODEL,
        vector_store_collection=retrieval_result.vector_store_collection or AI_VECTOR_COLLECTION,
        debug_message="Real RAG + LLM path completed",
        failure_reason=None,
        rag_details=rag_debug,
    )
    response = _apply_debug_to_response(response, debug_payload)
    response = _apply_cache_metadata(response, algorithm_signature=effective_signature, cache_hit=False)
    logger.info(
        "ai_analysis stage=completed mode=real citations=%s recommendations=%s",
        len(citations),
        len(response.recommendations),
    )
    return response, citations, nist_references


async def compute_and_persist_ai_analysis(scan_uuid: uuid_lib.UUID, db: Session) -> AiAnalysisResponse | None:
    logger.info("ai_analysis stage=task_start scan_uuid=%s", str(scan_uuid))
    findings = await fetch_findings(scan_uuid, db)
    if findings is None:
        logger.warning("ai_analysis stage=no_findings scan_uuid=%s", str(scan_uuid))
        return None

    deduped_findings = deduplicate_findings(findings)
    algorithm_signature = build_algorithm_signature(deduped_findings)

    if AI_CACHE_ENABLED:
        cached_snapshot = find_cached_snapshot_by_algorithm_signature(
            db,
            algorithm_signature=algorithm_signature,
            max_age_hours=AI_CACHE_MAX_AGE_HOURS,
            analysis_version=AI_ANALYSIS_VERSION,
        )
        if cached_snapshot is not None and cached_snapshot.scan_uuid != scan_uuid:
            cached_payload = serialize_ai_analysis_snapshot(cached_snapshot)
            cached_payload = _enrich_recommendations_for_code_fix(cached_payload, deduped_findings)
            cached_payload = _apply_cache_metadata(
                cached_payload,
                algorithm_signature=algorithm_signature,
                cache_hit=True,
                cache_source_scan=str(cached_snapshot.scan_uuid),
            )
            cached_payload = cached_payload.model_copy(
                update={
                    "analysis_mode": "real",
                    "debug_message": "Reused cached AI analysis for matching algorithm signature",
                    "failure_reason": None,
                }
            )
            cached_citations = list(cached_snapshot.citations or [])
            cached_refs = [
                ref.strip()
                for ref in str(cached_snapshot.nist_standard_reference or "").split(",")
                if ref.strip()
            ] or ["N/A"]
            upsert_ai_analysis_snapshot(
                db,
                scan_uuid,
                cached_payload,
                citations=cached_citations,
                nist_references=cached_refs,
                analysis_version=AI_ANALYSIS_VERSION,
            )
            logger.info(
                "ai_analysis stage=cache_hit scan_uuid=%s source_scan_uuid=%s signature=%s",
                str(scan_uuid),
                str(cached_snapshot.scan_uuid),
                algorithm_signature,
            )
            return cached_payload

    response, citations, nist_references = await analyze_findings(
        findings,
        algorithm_signature=algorithm_signature,
    )
    upsert_ai_analysis_snapshot(
        db,
        scan_uuid,
        response,
        citations=citations,
        nist_references=nist_references,
        analysis_version=AI_ANALYSIS_VERSION,
    )
    logger.info(
        "ai_analysis stage=persisted scan_uuid=%s mode=%s citations=%s",
        str(scan_uuid),
        response.analysis_mode,
        len(citations),
    )
    return response
