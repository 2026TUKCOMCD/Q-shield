from __future__ import annotations

from typing import Iterable

from app.severity_map import SEVERITY_SCORE

PUBLIC_EXPOSURE_KEYWORDS = ("auth", "login", "token", "jwt", "tls", "ssl", "cert", "nginx", "gateway")
HNDL_KEYWORDS = ("auth", "login", "token", "jwt", "cert", "certificate", "identity", "session", "gateway")
INTEROP_KEYWORDS = ("tls", "ssl", "cert", "certificate", "nginx", "gateway", "quic", "pkcs11", "hsm")
COMPLEXITY_KEYWORDS = ("config", "dependency", "library", "nginx", "gateway", "hsm", "pkcs11", "cert", "tls")
NON_PRODUCTION_KEYWORDS = (
    "test",
    "tests",
    "fixture",
    "fixtures",
    "example",
    "examples",
    "sample",
    "samples",
    "demo",
    "demos",
    "mock",
    "mocks",
)

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
    "hndl_bonus": {
        "label": "Harvest-now-decrypt-later sensitivity",
        "formula": "8 if auth/token/certificate/identity signal matched else 0",
        "source_basis": "long-lived confidential or identity-bound material should migrate earlier",
        "evidence_type": "nist_guidance_informed",
    },
    "migration_complexity_bonus": {
        "label": "Migration complexity",
        "formula": "0-8 based on config/dependency boundary signals and file spread",
        "source_basis": "complex migrations should be surfaced earlier for planning",
        "evidence_type": "engineering_heuristic",
    },
    "interop_risk_bonus": {
        "label": "Interoperability and deployment friction",
        "formula": "0-8 if TLS/certificate/HSM/QUIC boundary signal matched",
        "source_basis": "NIST SP 1800-38C emphasizes protocol and deployment compatibility risk",
        "evidence_type": "nist_guidance_informed",
    },
    "non_production_penalty": {
        "label": "Non-production path penalty",
        "formula": "-24 if all paths look like test/example fixtures, else -12 if mixed",
        "source_basis": "test and fixture assets should not outrank production migration targets",
        "evidence_type": "engineering_heuristic",
    },
}

PRIORITY_FACTOR_ORDER = (
    "severity_base",
    "class_risk_bonus",
    "evidence_bonus",
    "spread_bonus",
    "scanner_bonus",
    "exposure_bonus",
    "hndl_bonus",
    "migration_complexity_bonus",
    "interop_risk_bonus",
    "non_production_penalty",
)


def compute_priority_breakdown(
    *,
    class_key: str,
    max_severity: str,
    issue_count: int,
    affected_paths: Iterable[str],
    scanner_types: Iterable[str],
    contexts: Iterable[str],
    messages: Iterable[str],
    algorithm_label: str,
) -> dict[str, object]:
    normalized_paths = sorted({str(path) for path in affected_paths if path})
    production_paths = [path for path in normalized_paths if not is_non_production_path(path)]
    normalized_scanners = sorted({str(scanner) for scanner in scanner_types if scanner})
    normalized_contexts = sorted({str(context) for context in contexts if context})
    normalized_messages = sorted({str(message) for message in messages if message})

    severity_base = int(SEVERITY_SCORE.get(max_severity, SEVERITY_SCORE["MEDIUM"]) * 0.45)
    class_risk_bonus = int(CLASS_RISK_BONUS.get(class_key, CLASS_RISK_BONUS["library"]))
    evidence_bonus = min(18, int(issue_count) * 3)
    spread_bonus = min(15, len(normalized_paths) * 4)
    scanner_bonus = min(12, len(normalized_scanners) * 4)
    exposure_bonus = public_exposure_bonus(production_paths)
    hndl_bonus = hndl_bonus_score(production_paths, normalized_messages if production_paths else [])
    migration_complexity_bonus = migration_complexity_bonus_score(
        normalized_paths,
        normalized_scanners,
        normalized_contexts,
        issue_count,
    )
    interop_risk_bonus = interop_risk_bonus_score(
        production_paths,
        normalized_messages if production_paths else [],
        normalized_contexts if production_paths else [],
    )
    non_production_penalty = non_production_penalty_score(normalized_paths)

    total = (
        severity_base
        + class_risk_bonus
        + evidence_bonus
        + spread_bonus
        + scanner_bonus
        + exposure_bonus
        + hndl_bonus
        + migration_complexity_bonus
        + interop_risk_bonus
        + non_production_penalty
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
    if hndl_bonus > 0:
        reasons.append("possible HNDL-sensitive path")
    if migration_complexity_bonus > 0:
        reasons.append("migration complexity signal")
    if interop_risk_bonus > 0:
        reasons.append("interop-sensitive boundary")
    if non_production_penalty < 0:
        reasons.append("test/fixture path de-prioritized")

    return {
        "severity_base": severity_base,
        "class_risk_bonus": class_risk_bonus,
        "evidence_bonus": evidence_bonus,
        "spread_bonus": spread_bonus,
        "scanner_bonus": scanner_bonus,
        "exposure_bonus": exposure_bonus,
        "hndl_bonus": hndl_bonus,
        "migration_complexity_bonus": migration_complexity_bonus,
        "interop_risk_bonus": interop_risk_bonus,
        "non_production_penalty": non_production_penalty,
        "total": total,
        "reason": ", ".join(reasons),
        "priority_factors": build_priority_factors(
            severity_base=severity_base,
            class_risk_bonus=class_risk_bonus,
            evidence_bonus=evidence_bonus,
            spread_bonus=spread_bonus,
            scanner_bonus=scanner_bonus,
            exposure_bonus=exposure_bonus,
            hndl_bonus=hndl_bonus,
            migration_complexity_bonus=migration_complexity_bonus,
            interop_risk_bonus=interop_risk_bonus,
            non_production_penalty=non_production_penalty,
        ),
        "factor_notes": PRIORITY_FACTOR_NOTES,
    }


def public_exposure_bonus(paths: Iterable[str]) -> int:
    joined = " ".join(str(path) for path in paths).lower()
    return 10 if any(keyword in joined for keyword in PUBLIC_EXPOSURE_KEYWORDS) else 0


def hndl_bonus_score(paths: Iterable[str], messages: Iterable[str]) -> int:
    joined = " ".join([*(str(path) for path in paths), *(str(message) for message in messages)]).lower()
    return 8 if any(keyword in joined for keyword in HNDL_KEYWORDS) else 0


def migration_complexity_bonus_score(
    paths: Iterable[str],
    scanner_types: Iterable[str],
    contexts: Iterable[str],
    issue_count: int,
) -> int:
    joined = " ".join([*(str(path) for path in paths), *(str(context) for context in contexts)]).lower()
    score = 0
    if any(keyword in joined for keyword in COMPLEXITY_KEYWORDS):
        score += 4
    if len({str(scanner) for scanner in scanner_types if scanner}) >= 2:
        score += 2
    if int(issue_count) >= 3:
        score += 2
    return min(8, score)


def interop_risk_bonus_score(paths: Iterable[str], messages: Iterable[str], contexts: Iterable[str]) -> int:
    joined = " ".join(
        [*(str(path) for path in paths), *(str(message) for message in messages), *(str(context) for context in contexts)]
    ).lower()
    return 8 if any(keyword in joined for keyword in INTEROP_KEYWORDS) else 0


def is_non_production_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/").lower()
    segments = [segment for segment in normalized.split("/") if segment]
    return any(segment in NON_PRODUCTION_KEYWORDS for segment in segments)


def non_production_penalty_score(paths: Iterable[str]) -> int:
    normalized_paths = [str(path) for path in paths if path]
    if not normalized_paths:
        return 0

    non_production_paths = [path for path in normalized_paths if is_non_production_path(path)]
    if not non_production_paths:
        return 0
    if len(non_production_paths) == len(normalized_paths):
        return -24
    return -12


def build_priority_factors(**scores: int) -> list[dict[str, object]]:
    factors: list[dict[str, object]] = []
    for key in PRIORITY_FACTOR_ORDER:
        score = int(scores.get(key, 0) or 0)
        note = PRIORITY_FACTOR_NOTES[key]
        factors.append(
            {
                "key": key,
                "label": note["label"],
                "score": score,
                "formula": note["formula"],
                "source_basis": note["source_basis"],
                "evidence_type": note["evidence_type"],
            }
        )
    return factors
