from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from language_detector.repository_analyzer import RepositoryAnalyzer
from scanners.sast.scanner import SASTScanner


def _repo_root() -> Path:
    return ROOT.parent / "test_vulnerable_repo"


def test_sast_scanner_detects_known_patterns():
    repo_root = _repo_root()
    analyzer = RepositoryAnalyzer()
    analysis = analyzer.analyze(str(repo_root))
    report = SASTScanner().scan_repository(analysis.scanner_targets.sast_targets)

    by_path = {r.file_path: r for r in report.detailed_results if not r.skipped}

    py = by_path.get("vulnerable_crypto.py")
    assert py is not None
    py_types = {v.get("type") for v in py.vulnerabilities}
    assert "rsa_generation" in py_types
    assert "weak_hash" in py_types

    js = by_path.get("vulnerable_crypto.js")
    assert js is not None
    js_types = {v.get("type") for v in js.vulnerabilities}
    assert "rsa_generation" in js_types
    assert "ecdsa_generation" in js_types
    assert "crypto_require" in js_types


def test_sast_scanner_detects_python_jwt_signing_patterns():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "token_service.py").write_text(
            """
import jwt
from jose import jwt as jose_jwt

def issue_token(payload, key):
    token = jwt.encode(payload, key, algorithm="RS256")
    return jose_jwt.decode(token, key, algorithms=["ES256"])
""".strip(),
            encoding="utf-8",
        )

        analysis = RepositoryAnalyzer().analyze(str(repo))
        report = SASTScanner().scan_repository(analysis.scanner_targets.sast_targets)
        findings = report.detailed_results[0].vulnerabilities
        finding_types = {finding["type"] for finding in findings}

        assert "jwt_library_usage" in finding_types
        assert "jwt_rsa_algorithm" in finding_types
        assert "jwt_ecdsa_algorithm" in finding_types


def test_sast_scanner_detects_javascript_jwt_signing_patterns():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "auth.js").write_text(
            """
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

function sign(payload, privateKey) {
  crypto.createSign('RSA-SHA256');
  return jwt.sign(payload, privateKey, { algorithm: 'RS256' });
}
""".strip(),
            encoding="utf-8",
        )

        analysis = RepositoryAnalyzer().analyze(str(repo))
        report = SASTScanner().scan_repository(analysis.scanner_targets.sast_targets)
        findings = report.detailed_results[0].vulnerabilities
        finding_types = {finding["type"] for finding in findings}

        assert "jwt_library_usage" in finding_types
        assert "jwt_rsa_algorithm" in finding_types


def test_sast_scanner_detects_java_jwt_signing_patterns():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "JwtSigner.java").write_text(
            """
import io.jsonwebtoken.SignatureAlgorithm;
import java.security.Signature;

public class JwtSigner {
    public void sign() throws Exception {
        Signature signature = Signature.getInstance("SHA256withRSA");
        SignatureAlgorithm alg = SignatureAlgorithm.RS256;
    }
}
""".strip(),
            encoding="utf-8",
        )

        analysis = RepositoryAnalyzer().analyze(str(repo))
        report = SASTScanner().scan_repository(analysis.scanner_targets.sast_targets)
        findings = report.detailed_results[0].vulnerabilities
        finding_types = {finding["type"] for finding in findings}

        assert "jwt_library_usage" in finding_types
        assert "rsa_signature" in finding_types
        assert "jwt_rsa_algorithm" in finding_types
