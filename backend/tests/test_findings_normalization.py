import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import tasks


def test_normalize_findings_schema():
    sast_detail = SimpleNamespace(
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
            }
        ],
    )
    sast_report = SimpleNamespace(detailed_results=[sast_detail])

    sca_detail = SimpleNamespace(
        file_path="requirements.txt",
        vulnerable_dependencies=[
            {
                "name": "pycrypto",
                "current_version": "2.6.1",
                "dependency_type": "runtime",
                "severity": "HIGH",
                "reason": "RSA/DSA library without PQC support.",
                "pqc_support": False,
                "alternatives": [],
            }
        ],
    )
    sca_report = SimpleNamespace(detailed_results=[sca_detail])

    config_detail = SimpleNamespace(
        file_path="nginx.conf",
        findings=[
            {
                "type": "outdated_tls",
                "line": 1,
                "severity": "HIGH",
                "description": "Outdated TLS version",
                "matched_text": "TLSv1.0",
                "recommendation": "Upgrade to TLS 1.3",
            }
        ],
    )
    config_report = SimpleNamespace(detailed_results=[config_detail])

    findings = tasks._normalize_findings(sast_report, sca_report, config_report, None)
    assert len(findings) == 3

    for finding in findings:
        assert finding.get("type")
        assert finding.get("severity")
        assert "file_path" in finding
        assert "line_start" in finding and "line_end" in finding
        assert "evidence" in finding
        meta = finding.get("meta") or {}
        assert meta.get("scanner_type")
        assert meta.get("rule_id")
        assert "message" in meta
