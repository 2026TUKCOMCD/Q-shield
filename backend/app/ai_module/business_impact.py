from __future__ import annotations

from collections import Counter

from app.ai_module.schemas import RefactorCostEstimate


def estimate_refactor_cost(findings: list[dict]) -> RefactorCostEstimate:
    file_counter: Counter[str] = Counter()
    for finding in findings:
        file_path = str(finding.get("file_path") or "unknown")
        file_counter[file_path] += 1

    affected_files = len(file_counter)
    total_findings = sum(file_counter.values())
    usage_density = round(total_findings / max(affected_files, 1), 2) if total_findings else 0.0
    most_centralized = file_counter.most_common(1)[0][1] if file_counter else 0
    centralization_ratio = round(most_centralized / max(total_findings, 1), 2) if total_findings else 0.0
    distribution = "centralized" if centralization_ratio >= 0.6 else "distributed"

    score = 0
    if affected_files >= 10:
        score += 2
    elif affected_files >= 4:
        score += 1

    if usage_density >= 3:
        score += 2
    elif usage_density >= 1.5:
        score += 1

    if distribution == "distributed":
        score += 1

    if score >= 4:
        level = "HIGH"
    elif score >= 2:
        level = "MEDIUM"
    else:
        level = "LOW"

    explanation = (
        f"{affected_files} files affected, usage density {usage_density} findings/file, "
        f"{distribution} usage pattern (centralization ratio {centralization_ratio})."
    )
    return RefactorCostEstimate(level=level, explanation=explanation, affected_files=affected_files)
