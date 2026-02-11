from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from language_detector.repository_analyzer import RepositoryAnalyzer
from scanners.sca.scanner import SCAScanner


def _fixture_root() -> Path:
    return ROOT / "tests" / "fixtures" / "sca_project"


def test_sca_scanner_detects_vulnerable_dependencies():
    fixture_root = _fixture_root()
    analyzer = RepositoryAnalyzer()
    analysis = analyzer.analyze(str(fixture_root))
    report = SCAScanner().scan_repository(analysis.scanner_targets.sca_targets)

    names = set()
    for result in report.detailed_results:
        for dep in result.vulnerable_dependencies:
            names.add(dep.get("name"))

    assert "pycrypto" in names
    assert "cryptography" in names
    assert "python-rsa" in names
    assert "node-rsa" in names
    assert "jsrsasign" in names
    assert "org.bouncycastle.bcprov-jdk15on" in names


def test_sca_version_comparison_simple_cases():
    scanner = SCAScanner()
    assert scanner._is_version_vulnerable("1.2.0", ["<2.0.0"])
    assert scanner._is_version_vulnerable("1.2.0", ["<=1.2.0"])
    assert not scanner._is_version_vulnerable("2.0.0", ["<2.0.0"])
