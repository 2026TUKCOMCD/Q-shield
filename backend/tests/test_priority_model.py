import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.recommendation_priority import compute_priority_breakdown


def test_priority_breakdown_adds_exposure_and_scanner_corroboration():
    breakdown = compute_priority_breakdown(
        class_key="rsa",
        max_severity="HIGH",
        issue_count=2,
        affected_paths=["src/auth/token_service.py", "nginx/tls.conf"],
        scanner_types=["SAST", "SCA"],
        algorithm_label="RSA",
    )

    assert breakdown["severity_base"] == 36
    assert breakdown["class_risk_bonus"] == 18
    assert breakdown["evidence_bonus"] == 6
    assert breakdown["spread_bonus"] == 8
    assert breakdown["scanner_bonus"] == 8
    assert breakdown["exposure_bonus"] == 10
    assert breakdown["total"] == 86
    assert "RSA class risk" in breakdown["reason"]
    assert "signals from SAST, SCA" in breakdown["reason"]
    assert "auth/tls-facing usage" in breakdown["reason"]
