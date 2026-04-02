from __future__ import annotations

from typing import Iterable

from app.severity_map import SEVERITY_SCORE

PUBLIC_EXPOSURE_KEYWORDS = ("auth", "login", "token", "jwt", "tls", "ssl", "cert", "nginx", "gateway")

CLASS_RISK_BONUS = {
    "rsa": 18,
    "dh": 17,
    "ecc": 18,
    "dsa": 16,
    "sha-1": 8,
    "library": 10,
}

PRIORITY_FACTOR_NOTES = {
    "severity_base": {
        "label": "Finding severity",
        "formula": "int(SEVERITY_SCORE[max_severity] * 0.45)",
        "source_basis": "scanner severity normalization",
        "evidence_type": "engineering_heuristic",
    },
    "class_risk_bonus": {
        "label": "Quantum-vulnerable algorithm class",
        "formula": "CLASS_RISK_BONUS[class_key]",
        "source_basis": "NIST IR 8547 + FIPS 203/204/205 transition focus on public-key migration",
        "evidence_type": "nist_guidance_informed",
    },
    "evidence_bonus": {
        "label": "Evidence count",
        "formula": "min(18, issue_count * 3)",
        "source_basis": "multiple findings increase confidence and remediation pressure",
        "evidence_type": "engineering_heuristic",
    },
    "spread_bonus": {
        "label": "Blast radius",
        "formula": "min(15, affected_files * 4)",
        "source_basis": "broader file spread implies larger migration scope",
        "evidence_type": "engineering_heuristic",
    },
    "scanner_bonus": {
        "label": "Cross-scanner corroboration",
        "formula": "min(12, scanner_types * 4)",
        "source_basis": "SAST/SCA/Config agreement increases actionability",
        "evidence_type": "engineering_heuristic",
    },
    "exposure_bonus": {
        "label": "External exposure",
        "formula": "10 if auth/tls/token/cert path keyword matched else 0",
        "source_basis": "internet-facing auth/tls usage has higher migration urgency",
        "evidence_type": "nist_guidance_informed",
    },
}


def compute_priority_breakdown(
    *,
    class_key: str,
    max_severity: str,
    issue_count: int,
    affected_paths: Iterable[str],
    scanner_types: Iterable[str],
    algorithm_label: str,
) -> dict[str, object]:
    normalized_paths = sorted({str(path) for path in affected_paths if path})
    normalized_scanners = sorted({str(scanner) for scanner in scanner_types if scanner})

    severity_base = int(SEVERITY_SCORE.get(max_severity, SEVERITY_SCORE["MEDIUM"]) * 0.45)
    class_risk_bonus = int(CLASS_RISK_BONUS.get(class_key, CLASS_RISK_BONUS["library"]))
    evidence_bonus = min(18, int(issue_count) * 3)
    spread_bonus = min(15, len(normalized_paths) * 4)
    scanner_bonus = min(12, len(normalized_scanners) * 4)
    exposure_bonus = public_exposure_bonus(normalized_paths)

    total = (
        severity_base
        + class_risk_bonus
        + evidence_bonus
        + spread_bonus
        + scanner_bonus
        + exposure_bonus
    )

    reasons = [
        f"{algorithm_label} class risk",
        f"{max_severity} severity",
        f"{issue_count} evidence points",
    ]
    if normalized_paths:
        reasons.append(f"{len(normalized_paths)} affected files")
    if normalized_scanners:
        reasons.append(f"signals from {', '.join(normalized_scanners)}")
    if exposure_bonus > 0:
        reasons.append("auth/tls-facing usage")

    return {
        "severity_base": severity_base,
        "class_risk_bonus": class_risk_bonus,
        "evidence_bonus": evidence_bonus,
        "spread_bonus": spread_bonus,
        "scanner_bonus": scanner_bonus,
        "exposure_bonus": exposure_bonus,
        "total": total,
        "reason": ", ".join(reasons),
        "factor_notes": PRIORITY_FACTOR_NOTES,
    }


def public_exposure_bonus(paths: Iterable[str]) -> int:
    joined = " ".join(str(path) for path in paths).lower()
    return 10 if any(keyword in joined for keyword in PUBLIC_EXPOSURE_KEYWORDS) else 0
