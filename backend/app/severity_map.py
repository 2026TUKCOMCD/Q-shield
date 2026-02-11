from __future__ import annotations

from typing import Tuple

CANONICAL_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")

SEVERITY_SCORE = {
    "CRITICAL": 100,
    "HIGH": 80,
    "MEDIUM": 50,
    "LOW": 20,
    "INFO": 5,
}

_SEVERITY_ALIASES = {
    "CRITICAL": "CRITICAL",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "INFO": "INFO",
    "WARN": "MEDIUM",
    "WARNING": "MEDIUM",
    "SEVERE": "HIGH",
}


def canonicalize_severity(value: str | None) -> Tuple[str, int]:
    if not value:
        return "MEDIUM", SEVERITY_SCORE["MEDIUM"]
    normalized = str(value).strip().upper()
    canonical = _SEVERITY_ALIASES.get(normalized, "MEDIUM")
    return canonical, SEVERITY_SCORE[canonical]
