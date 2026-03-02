import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.scoring import (
    build_score_signals_from_findings,
    compute_pqc_readiness_score,
    compute_risk_score,
    compute_severity_weighted_index,
)


def test_scoring_functions_are_deterministic_for_known_findings():
    findings = [
        {
            "type": "rsa_generation",
            "severity": "HIGH",
            "algorithm": "RSA",
            "meta": {"scanner_type": "SAST", "rule_id": "rsa_generation"},
        },
        {
            "type": "node-rsa",
            "severity": "MEDIUM",
            "algorithm": None,
            "meta": {"scanner_type": "SCA", "rule_id": "node-rsa", "library": "node-rsa"},
        },
    ]

    signals = build_score_signals_from_findings(findings)

    assert compute_pqc_readiness_score(signals, scale=10) == 7
    assert compute_pqc_readiness_score(signals, scale=100) == 70
    assert compute_risk_score(signals) == 30
    assert compute_severity_weighted_index(signals) == 4.0
