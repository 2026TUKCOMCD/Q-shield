from __future__ import annotations

from collections import Counter

from app.scoring import (
    build_score_signals_from_findings,
    compute_pqc_readiness_score,
    compute_risk_score,
    compute_severity_weighted_index,
)


def deduplicate_findings(findings: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    deduped: list[dict] = []

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        meta = finding.get("meta") or {}
        key = (
            finding.get("type"),
            finding.get("severity"),
            finding.get("algorithm"),
            finding.get("file_path"),
            finding.get("line_start"),
            finding.get("line_end"),
            meta.get("rule_id"),
            meta.get("scanner_type"),
            finding.get("evidence"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def summarize_inputs(findings: list[dict], *, source_count: int | None = None) -> dict:
    scanner_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    total_source_count = source_count if source_count is not None else len(findings)
    duplicate_count = max(0, total_source_count - len(findings))

    for finding in findings:
        meta = finding.get("meta") or {}
        scanner_counts[str(meta.get("scanner_type") or finding.get("context") or "UNKNOWN")] += 1
        severity_counts[str(finding.get("severity") or "UNKNOWN")] += 1
        rule_counts[str(meta.get("rule_id") or finding.get("type") or "unknown")] += 1
        duplicate_count += max(0, int(meta.get("duplicate_count", 1)) - 1)

    duplicate_ratio = 0.0
    if total_source_count > 0:
        duplicate_ratio = round(duplicate_count / total_source_count, 4)

    return {
        "total_findings": len(findings),
        "source_findings": total_source_count,
        "counts_by_scanner_type": dict(scanner_counts),
        "counts_by_severity": dict(severity_counts),
        "top_rules": [rule for rule, _ in rule_counts.most_common(5)],
        "duplicate_ratio": duplicate_ratio,
    }


def compute_risk_metrics(findings: list[dict]) -> dict[str, int | float]:
    signals = build_score_signals_from_findings(findings)
    return {
        "risk_score": compute_risk_score(signals),
        "pqc_readiness_score": compute_pqc_readiness_score(signals, scale=100),
        "severity_weighted_index": compute_severity_weighted_index(signals),
    }
