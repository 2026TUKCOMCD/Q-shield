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


def test_recommendations_group_similar_findings_by_class():
    sast_detail = SimpleNamespace(
        file_path="src/auth.py",
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
                "type": "rsa_encrypt",
                "line": 20,
                "severity": "MEDIUM",
                "algorithm": "RSA",
                "description": "RSA encryption detected",
                "recommendation": "Use PQC-safe alternatives",
                "code": "cipher.encrypt(data)",
            },
        ],
    )
    sca_detail = SimpleNamespace(
        file_path="requirements.txt",
        vulnerable_dependencies=[
            {
                "name": "python-rsa",
                "current_version": "4.0",
                "dependency_type": "runtime",
                "severity": "HIGH",
                "reason": "Legacy RSA dependency",
            }
        ],
    )
    config_detail = SimpleNamespace(
        file_path="nginx.conf",
        findings=[
            {
                "type": "sha1_signature",
                "line": 1,
                "severity": "HIGH",
                "description": "SHA-1 usage detected",
                "recommendation": "Remove SHA-1",
            }
        ],
    )

    recommendations = tasks._extract_recommendations(
        SimpleNamespace(detailed_results=[sast_detail]),
        SimpleNamespace(detailed_results=[sca_detail]),
        SimpleNamespace(detailed_results=[config_detail]),
    )

    assert len(recommendations) == 2
    assert recommendations[0]["algorithm"] in {"RSA", "Weak Hash"}
    assert any(rec["algorithm"] == "RSA" for rec in recommendations)
    assert any(rec["algorithm"] == "Weak Hash" for rec in recommendations)
