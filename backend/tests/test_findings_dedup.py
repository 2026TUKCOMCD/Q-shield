import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import tasks
from app.recommendation_planner import build_recommendation_plan


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
    assert meta.get("asset_ref") == "code:rsa-public-key:src/app.py"
    assert meta.get("correlation_ref") == "rsa-public-key:general"


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


def test_recommendations_store_all_distinct_vulnerability_classes():
    sast_detail = SimpleNamespace(
        file_path="src/crypto.py",
        vulnerabilities=[
            {
                "type": "rsa_generation",
                "line": 10,
                "severity": "HIGH",
                "algorithm": "RSA",
                "description": "RSA detected",
                "recommendation": "Replace RSA",
                "code": "RSA.generate(2048)",
            },
            {
                "type": "dh_exchange",
                "line": 20,
                "severity": "HIGH",
                "algorithm": "DH",
                "description": "DH detected",
                "recommendation": "Replace DH",
                "code": "dh.exchange()",
            },
            {
                "type": "ecdsa_signature",
                "line": 30,
                "severity": "HIGH",
                "algorithm": "ECDSA",
                "description": "ECDSA detected",
                "recommendation": "Replace ECDSA",
                "code": "ecdsa.sign()",
            },
            {
                "type": "dsa_signature",
                "line": 40,
                "severity": "MEDIUM",
                "algorithm": "DSA",
                "description": "DSA detected",
                "recommendation": "Replace DSA",
                "code": "dsa.sign()",
            },
            {
                "type": "weak_hash",
                "line": 50,
                "severity": "HIGH",
                "algorithm": "SHA-1",
                "description": "SHA-1 detected",
                "recommendation": "Remove SHA-1",
                "code": "sha1(data)",
            },
        ],
    )
    sca_detail = SimpleNamespace(
        file_path="requirements.txt",
        vulnerable_dependencies=[
            {
                "name": "legacy-crypto-lib",
                "current_version": "1.0",
                "dependency_type": "runtime",
                "severity": "MEDIUM",
                "reason": "No PQC support",
            }
        ],
    )

    recommendations = tasks._extract_recommendations(
        SimpleNamespace(detailed_results=[sast_detail]),
        SimpleNamespace(detailed_results=[sca_detail]),
        SimpleNamespace(detailed_results=[]),
    )

    algorithms = {rec["algorithm"] for rec in recommendations}
    assert len(recommendations) == 6
    assert algorithms == {"RSA", "DH/ECDH", "ECC/ECDSA", "DSA", "Weak Hash", "Legacy Library"}


def test_recommendation_plan_adds_priority_reason_and_evidence_summary():
    findings = [
        {
            "type": "jwt_rsa_algorithm",
            "severity": "HIGH",
            "algorithm": "RSA",
            "context": "SAST",
            "file_path": "src/auth/token_service.py",
            "line_start": 12,
            "line_end": 12,
            "evidence": 'jwt.encode(payload, key, algorithm="RS256")',
            "meta": {
                "scanner_type": "SAST",
                "rule_id": "jwt_rsa_algorithm",
                "message": "RSA-based JWT/JOSE signing algorithm detected.",
                "usage_type": "code",
                "duplicate_count": 1,
            },
        },
        {
            "type": "python-jose",
            "severity": "HIGH",
            "algorithm": None,
            "context": "SCA",
            "file_path": "pyproject.toml",
            "line_start": None,
            "line_end": None,
            "evidence": "python-jose==3.3.0",
            "meta": {
                "scanner_type": "SCA",
                "rule_id": "python-jose",
                "message": "JOSE/JWT library built around traditional RSA/ECDSA algorithms without PQC support.",
                "usage_type": "dependency",
                "library": "python-jose",
                "duplicate_count": 1,
            },
        },
    ]

    plan = build_recommendation_plan(findings)

    assert len(plan) == 1
    rsa_item = plan[0]
    assert rsa_item["normalized_class"] == "rsa-public-key"
    assert rsa_item["evidence_count"] == 2
    assert rsa_item["affected_files_count"] == 2
    assert set(rsa_item["scanner_types"]) == {"SAST", "SCA"}
    assert len(rsa_item["priority_factors"]) == 9
    assert any(factor["key"] == "hndl_bonus" for factor in rsa_item["priority_factors"])
    assert "code:rsa-public-key:src/auth/token_service.py" in rsa_item["related_asset_refs"]
    assert "dependency:rsa-public-key:pyproject.toml#python-jose" in rsa_item["related_asset_refs"]
    assert "rsa-public-key:auth-token" in rsa_item["correlation_refs"]
    assert "RSA class risk" in rsa_item["priority_reason"]
    assert "auth/tls-facing usage" in rsa_item["priority_reason"]
    assert "possible HNDL-sensitive path" in rsa_item["priority_reason"]
    assert "migration complexity signal" in rsa_item["priority_reason"]
