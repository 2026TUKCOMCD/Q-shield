from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from language_detector.repository_analyzer import RepositoryAnalyzer
from scanners.config.scanner import ConfigScanner


def _fixture_root() -> Path:
    return ROOT / "tests" / "fixtures" / "config_project"


def test_config_scanner_detects_tls_issues():
    fixture_root = _fixture_root()
    analyzer = RepositoryAnalyzer()
    analysis = analyzer.analyze(str(fixture_root))
    report = ConfigScanner().scan_repository(analysis.scanner_targets.config_targets)

    types = set()
    for result in report.detailed_results:
        for finding in result.findings:
            types.add(finding.get("type"))

    assert "outdated_tls" in types
    assert "rsa_cipher" in types
    assert "ecdsa_cipher" in types
