import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import tasks


def test_dedup_drops_exact_duplicates_and_counts():
    detail = SimpleNamespace(
        file_path="src/app.py",
        vulnerabilities=[
            {
                "type": "rsa_generation",
                "line": 10,
                "severity": "HIGH",
                "algorithm": "RSA",
                "description": "RSA key generation detected",
                "recommendation": "Use PQC-safe alternatives",
                "code": "RSA.generate(2048)",
            },
            {
                "type": "rsa_generation",
                "line": 10,
                "severity": "HIGH",
                "algorithm": "RSA",
                "description": "RSA key generation detected",
                "recommendation": "Use PQC-safe alternatives",
                "code": "RSA.generate(2048)",
            },
        ],
    )
    sast_report = SimpleNamespace(detailed_results=[detail])
    sca_report = SimpleNamespace(detailed_results=[])
    config_report = SimpleNamespace(detailed_results=[])

    findings = tasks._normalize_findings(sast_report, sca_report, config_report, None)
    assert len(findings) == 1
    meta = findings[0].get("meta") or {}
    assert meta.get("duplicate_count") == 2


def test_dedup_keeps_distinct_rule_ids():
    detail = SimpleNamespace(
        file_path="src/app.py",
        vulnerabilities=[
            {
                "type": "rsa_generation",
                "line": 10,
                "severity": "HIGH",
                "algorithm": "RSA",
                "description": "RSA key generation detected",
                "recommendation": "Use PQC-safe alternatives",
                "code": "RSA.generate(2048)",
            },
            {
                "type": "weak_random",
                "line": 10,
                "severity": "MEDIUM",
                "algorithm": "RNG",
                "description": "Weak random detected",
                "recommendation": "Use secure RNG",
                "code": "random()",
            },
        ],
    )
    sast_report = SimpleNamespace(detailed_results=[detail])
    sca_report = SimpleNamespace(detailed_results=[])
    config_report = SimpleNamespace(detailed_results=[])

    findings = tasks._normalize_findings(sast_report, sca_report, config_report, None)
    assert len(findings) == 2
