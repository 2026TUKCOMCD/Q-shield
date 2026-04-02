from __future__ import annotations

import re

from app.ai_module.schemas import AiAnalysisResponse

PERCENTAGE_SENTENCE_PATTERN = re.compile(r"[^.\n]*?(?:\d+\s*%|percent)[^.\n]*[.\n]?", re.IGNORECASE)
NORMATIVE_CLAIM_TYPES = {"normative", "migration_guidance", "risk_guidance"}
BENCHMARK_CLAIM_TYPES = {"benchmark", "benchmark_guidance"}


def _sanitize_percentage_claims(text: str | None) -> tuple[str, int]:
    raw = str(text or "")
    matches = list(PERCENTAGE_SENTENCE_PATTERN.finditer(raw))
    if not matches:
        return raw, 0

    sanitized = PERCENTAGE_SENTENCE_PATTERN.sub("", raw)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
    if not sanitized:
        sanitized = "Quantified security improvement claim removed pending authoritative evidence."
    return sanitized, len(matches)


def _citation_claim_types(recommendation) -> set[str]:
    return {
        str(citation.claim_type or "").strip()
        for citation in recommendation.citations
        if str(citation.claim_type or "").strip()
    }


def _has_normative_citation(recommendation) -> bool:
    return any(claim_type in NORMATIVE_CLAIM_TYPES for claim_type in _citation_claim_types(recommendation))


def _has_only_benchmark_citations(recommendation) -> bool:
    claim_types = _citation_claim_types(recommendation)
    return bool(claim_types) and claim_types.issubset(BENCHMARK_CLAIM_TYPES)


def validate_ai_response(response: AiAnalysisResponse) -> AiAnalysisResponse:
    summary, summary_claims_removed = _sanitize_percentage_claims(response.analysis_summary)
    validation_report = {
        "percentage_claims_removed": summary_claims_removed,
        "benchmark_only_reference_downgrades": 0,
        "recommendations_reviewed": len(response.recommendations),
    }

    updated_recommendations = []
    for recommendation in response.recommendations:
        description, description_claims_removed = _sanitize_percentage_claims(recommendation.description)
        benchmark_notes = []
        benchmark_claims_removed = 0
        for note in recommendation.benchmark_notes:
            sanitized_note, removed_count = _sanitize_percentage_claims(note)
            if sanitized_note:
                benchmark_notes.append(sanitized_note)
            benchmark_claims_removed += removed_count

        confidence = recommendation.confidence
        confidence_reason_parts = [part.strip() for part in str(recommendation.confidence_reason or "").split(",") if part.strip()]

        nist_standard_reference = recommendation.nist_standard_reference
        if recommendation.citations and _has_only_benchmark_citations(recommendation):
            nist_standard_reference = "N/A"
            confidence = round(max(0.0, confidence - 0.15), 4)
            validation_report["benchmark_only_reference_downgrades"] += 1
            confidence_reason_parts.append("normative reference removed because only benchmark citations were attached")
        elif recommendation.citations and not _has_normative_citation(recommendation):
            confidence = round(max(0.0, confidence - 0.1), 4)
            confidence_reason_parts.append("confidence reduced because no normative citation was attached")

        removed_total = description_claims_removed + benchmark_claims_removed
        if removed_total:
            confidence = round(max(0.0, confidence - 0.1), 4)
            validation_report["percentage_claims_removed"] += removed_total
            confidence_reason_parts.append("unsupported quantified security claim removed")

        updated_recommendations.append(
            recommendation.model_copy(
                update={
                    "description": description,
                    "benchmark_notes": benchmark_notes,
                    "nist_standard_reference": nist_standard_reference,
                    "confidence": confidence,
                    "confidence_reason": ", ".join(dict.fromkeys(confidence_reason_parts)),
                }
            )
        )

    updated_inputs_summary = dict(response.inputs_summary or {})
    updated_inputs_summary["validation"] = validation_report

    updated_response = response.model_copy(
        update={
            "analysis_summary": summary,
            "recommendations": updated_recommendations,
            "inputs_summary": updated_inputs_summary,
        }
    )

    if validation_report["percentage_claims_removed"] > 0 or validation_report["benchmark_only_reference_downgrades"] > 0:
        adjusted_confidence = round(max(0.0, updated_response.confidence_score - 0.1), 4)
        return updated_response.model_copy(update={"confidence_score": adjusted_confidence})
    return updated_response
