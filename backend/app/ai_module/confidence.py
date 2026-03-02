from __future__ import annotations


def compute_confidence_score(
    *,
    findings: list[dict],
    inputs_summary: dict,
    citation_missing: bool,
    citations_count: int,
) -> float:
    if not findings:
        return 0.0

    finding_factor = min(0.35, len(findings) * 0.04)
    scanner_types = inputs_summary.get("counts_by_scanner_type") or {}
    active_scanners = sum(1 for count in scanner_types.values() if count)
    consistency_factor = min(0.25, active_scanners * 0.08)
    duplicate_ratio = float(inputs_summary.get("duplicate_ratio", 0.0) or 0.0)
    duplicate_penalty = min(0.15, duplicate_ratio * 0.3)
    citation_factor = 0.25 if citations_count else 0.0
    citation_penalty = 0.2 if citation_missing else 0.0

    score = 0.25 + finding_factor + consistency_factor + citation_factor - duplicate_penalty - citation_penalty
    return round(max(0.0, min(1.0, score)), 4)
