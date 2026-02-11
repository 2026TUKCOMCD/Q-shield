from pathlib import Path
import sys

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
