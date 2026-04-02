from __future__ import annotations

from typing import Iterable

from app.severity_map import SEVERITY_SCORE, canonicalize_severity

SEVERITY_WEIGHT = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "INFO": 0,
}

TEMPLATES = {
    "rsa": {
        "normalized_class": "rsa-public-key",
        "title": "Replace RSA-based cryptography with PQC-safe alternatives",
        "body": "RSA usage indicates quantum-vulnerable public-key cryptography. Prioritize ML-KEM for key establishment and ML-DSA for signature paths, depending on the usage context.",
        "algorithm": "RSA",
        "recommended_pqc_algorithm": "ML-KEM / ML-DSA",
        "estimated_effort": "5-8 M/D",
        "algorithm_bonus": 18,
    },
    "dh": {
        "normalized_class": "dh-key-exchange",
        "title": "Replace DH/ECDH key exchange with ML-KEM",
        "body": "Diffie-Hellman style key exchange remains vulnerable to quantum attacks. Plan a phased migration to ML-KEM-capable libraries and protocol negotiation paths.",
        "algorithm": "DH/ECDH",
        "recommended_pqc_algorithm": "ML-KEM",
        "estimated_effort": "5-8 M/D",
        "algorithm_bonus": 17,
    },
    "ecc": {
        "normalized_class": "ecc-signature",
        "title": "Replace ECC/ECDSA signature paths with ML-DSA",
        "body": "ECC and ECDSA-based signatures are not quantum-resistant. Identify signature boundaries first, then migrate verification and signing paths toward ML-DSA-compatible abstractions.",
        "algorithm": "ECC/ECDSA",
        "recommended_pqc_algorithm": "ML-DSA",
        "estimated_effort": "4-7 M/D",
        "algorithm_bonus": 18,
    },
    "dsa": {
        "normalized_class": "dsa-signature",
        "title": "Replace DSA signature usage with ML-DSA",
        "body": "Legacy DSA usage should be removed from signing workflows and key management paths in favor of PQC-safe signature algorithms.",
        "algorithm": "DSA",
        "recommended_pqc_algorithm": "ML-DSA",
        "estimated_effort": "3-5 M/D",
        "algorithm_bonus": 16,
    },
    "sha-1": {
        "normalized_class": "weak-hash",
        "title": "Remove weak hash usage before PQC migration",
        "body": "Weak hash functions such as SHA-1 or MD5 should be eliminated early because they increase migration debt and undermine transition trustworthiness.",
        "algorithm": "Weak Hash",
        "recommended_pqc_algorithm": "SHA-256 / SHA-3",
        "estimated_effort": "1-3 M/D",
        "algorithm_bonus": 8,
    },
    "library": {
        "normalized_class": "legacy-library",
        "title": "Replace legacy crypto libraries with PQC-capable dependencies",
        "body": "Some dependencies appear to lack a clear PQC support path. Consolidate crypto abstractions and prioritize libraries with vendor-backed or liboqs-based transition support.",
        "algorithm": "Legacy Library",
        "recommended_pqc_algorithm": "PQC-capable dependency stack",
        "estimated_effort": "3-6 M/D",
        "algorithm_bonus": 10,
    },
}


def build_recommendation_plan(findings: Iterable[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}

    for finding in findings or []:
        if not isinstance(finding, dict):
            continue

        key = classify_vulnerability_class(finding)
        template = TEMPLATES.get(key, TEMPLATES["library"])
        meta = finding.get("meta") or {}
        severity = canonicalize_severity(finding.get("severity"))[0]
        file_path = _to_text(finding.get("file_path"))
        scanner_type = _to_text(meta.get("scanner_type")) or _to_text(finding.get("context")) or "UNKNOWN"

        bucket = grouped.setdefault(
            key,
            {
                "template": template,
                "max_severity": "INFO",
                "issue_count": 0,
                "paths": set(),
                "scanner_types": set(),
                "messages": set(),
                "contexts": set(),
            },
        )
        if SEVERITY_WEIGHT[severity] > SEVERITY_WEIGHT[bucket["max_severity"]]:
            bucket["max_severity"] = severity
        bucket["issue_count"] += int(meta.get("duplicate_count", 1) or 1)
        if file_path:
            bucket["paths"].add(file_path)
        if scanner_type:
            bucket["scanner_types"].add(scanner_type)
        if meta.get("message"):
            bucket["messages"].add(str(meta["message"]))
        if meta.get("usage_type"):
            bucket["contexts"].add(str(meta["usage_type"]))

    ranked: list[dict] = []
    for key, bucket in grouped.items():
        template = bucket["template"]
        affected_paths = sorted(bucket["paths"])
        scanner_types = sorted(bucket["scanner_types"])
        score, reason = _compute_priority_score(
            key=key,
            max_severity=bucket["max_severity"],
            issue_count=bucket["issue_count"],
            affected_paths=affected_paths,
            scanner_types=scanner_types,
        )
        ranked.append(
            {
                "class_key": key,
                "normalized_class": template["normalized_class"],
                "title": template["title"],
                "algorithm": template["algorithm"],
                "recommended_pqc_algorithm": template["recommended_pqc_algorithm"],
                "estimated_effort": template["estimated_effort"],
                "priority_score": score,
                "priority_reason": reason,
                "evidence_count": bucket["issue_count"],
                "affected_files_count": len(affected_paths),
                "affected_file_paths": affected_paths,
                "scanner_types": scanner_types,
                "context": ", ".join(affected_paths[:3]) if affected_paths else "repository-wide",
                "ai_recommendation": _build_recommendation_markdown(
                    template=template,
                    issue_count=bucket["issue_count"],
                    affected_paths=affected_paths,
                    scanner_types=scanner_types,
                    priority_reason=reason,
                ),
            }
        )

    ranked.sort(
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["affected_files_count"]),
            -int(item["evidence_count"]),
            item["class_key"],
        )
    )

    for index, item in enumerate(ranked, start=1):
        item["priority_rank"] = index
        item["priority"] = rank_to_priority(index)

    return ranked


def classify_vulnerability_class(finding: dict) -> str:
    meta = finding.get("meta") or {}
    algorithm_text = _to_text(finding.get("algorithm")).lower()
    rule_text = _to_text(meta.get("rule_id") or finding.get("type")).lower()
    library_text = _to_text(meta.get("library")).lower()
    message_text = _to_text(meta.get("message")).lower()
    merged = " ".join((algorithm_text, rule_text, library_text, message_text))

    if "rsa" in merged or "rs256" in merged or "ps256" in merged:
        return "rsa"
    if any(token in merged for token in ("dh", "ecdh", "diffie")):
        return "dh"
    if any(token in merged for token in ("ecc", "ecdsa", "elliptic", "es256", "es384", "es512")):
        return "ecc"
    if "dsa" in merged:
        return "dsa"
    if any(token in merged for token in ("sha-1", "sha1", "md5", "weak hash")):
        return "sha-1"
    return "library"


def rank_to_priority(rank: int) -> str:
    if rank <= 2:
        return "CRITICAL"
    if rank <= 5:
        return "HIGH"
    if rank <= 8:
        return "MEDIUM"
    return "LOW"


def _compute_priority_score(
    *,
    key: str,
    max_severity: str,
    issue_count: int,
    affected_paths: list[str],
    scanner_types: list[str],
) -> tuple[int, str]:
    template = TEMPLATES.get(key, TEMPLATES["library"])
    base = int(SEVERITY_SCORE.get(max_severity, SEVERITY_SCORE["MEDIUM"]) * 0.45)
    evidence_bonus = min(18, int(issue_count) * 3)
    spread_bonus = min(15, len(affected_paths) * 4)
    scanner_bonus = min(12, len(scanner_types) * 4)
    exposure_bonus = _public_exposure_bonus(affected_paths)
    score = base + template["algorithm_bonus"] + evidence_bonus + spread_bonus + scanner_bonus + exposure_bonus

    reasons = [
        f"{template['algorithm']} class risk",
        f"{max_severity} severity",
        f"{issue_count} evidence points",
    ]
    if affected_paths:
        reasons.append(f"{len(affected_paths)} affected files")
    if scanner_types:
        reasons.append(f"signals from {', '.join(scanner_types)}")
    if exposure_bonus > 0:
        reasons.append("auth/tls-facing usage")

    return score, ", ".join(reasons)


def _public_exposure_bonus(paths: list[str]) -> int:
    joined = " ".join(paths).lower()
    keywords = ("auth", "login", "token", "jwt", "tls", "ssl", "cert", "nginx", "gateway")
    return 10 if any(keyword in joined for keyword in keywords) else 0


def _build_recommendation_markdown(
    *,
    template: dict,
    issue_count: int,
    affected_paths: list[str],
    scanner_types: list[str],
    priority_reason: str,
) -> str:
    affected_preview = ", ".join(affected_paths[:5]) if affected_paths else "repository-wide"
    scanner_preview = ", ".join(scanner_types) if scanner_types else "unknown"
    return (
        f"## {template['title']}\n"
        f"{template['body']}\n\n"
        f"Priority rationale: {priority_reason}\n"
        f"Affected files: {len(affected_paths)} ({affected_preview})\n"
        f"Detected issues: {issue_count}\n"
        f"Evidence sources: {scanner_preview}"
    )


def _to_text(value) -> str:
    return "" if value is None else str(value)
