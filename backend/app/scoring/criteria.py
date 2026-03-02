from __future__ import annotations

from app.severity_map import canonicalize_severity

SEVERITY_WEIGHT = {
    "CRITICAL": 4.0,
    "HIGH": 3.0,
    "MEDIUM": 2.0,
    "LOW": 1.0,
    "INFO": 0.5,
}

PUBLIC_KEY_KEYWORDS = ("rsa", "ecc", "ecdsa", "dsa", "dh", "diffie")
WEAK_HASH_KEYWORDS = ("md5", "sha1", "sha-1", "weak hash")
SYMMETRIC_KEYWORDS = ("aes", "chacha", "symmetric")


def algorithm_weight(algorithm: str | None) -> float:
    if not algorithm:
        return 1.0
    text = str(algorithm).lower()
    if any(keyword in text for keyword in PUBLIC_KEY_KEYWORDS):
        return 1.6
    if any(keyword in text for keyword in WEAK_HASH_KEYWORDS):
        return 1.3
    if any(keyword in text for keyword in SYMMETRIC_KEYWORDS):
        return 1.0
    return 1.0


def score_signal_points(severity: str | None, algorithm: str | None) -> float:
    canonical_severity, _ = canonicalize_severity(severity)
    return SEVERITY_WEIGHT.get(canonical_severity, SEVERITY_WEIGHT["MEDIUM"]) * algorithm_weight(algorithm)


def infer_algorithm_from_library(name: str | None) -> str | None:
    if not name:
        return None
    text = str(name).lower()
    if any(keyword in text for keyword in ("rsa", "node-rsa", "python-rsa")):
        return "RSA"
    if any(keyword in text for keyword in ("ecdsa", "ecc", "elliptic")):
        return "ECC/ECDSA"
    if any(keyword in text for keyword in ("dsa", "dh", "diffie")):
        return "DSA/DH"
    if any(keyword in text for keyword in ("sha1", "sha-1", "md5")):
        return "Weak Hash"
    return None
