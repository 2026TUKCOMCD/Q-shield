from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from language_detector.file_classifier import FileClassifier
from language_detector.repository_analyzer import RepositoryAnalyzer
from models.file_metadata import FileCategory, FileMetadata
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


def test_sca_scanner_detects_pyproject_dependencies():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "pyproject.toml").write_text(
            """
[project]
dependencies = ["authlib>=1.3.0", "python-jose[cryptography]==3.3.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
""".strip(),
            encoding="utf-8",
        )

        analysis = RepositoryAnalyzer().analyze(str(repo))
        report = SCAScanner().scan_repository(analysis.scanner_targets.sca_targets)

        names = {
            dep.get("name")
            for result in report.detailed_results
            for dep in result.vulnerable_dependencies
        }

        assert "authlib" in names
        assert "python-jose" in names


def test_sca_scanner_detects_gradle_dependencies():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "build.gradle").write_text(
            """
dependencies {
    implementation 'io.jsonwebtoken:jjwt-api:0.12.5'
    runtimeOnly "io.jsonwebtoken:jjwt-impl:0.12.5"
    implementation group: 'org.bitbucket.b_c', name: 'jose4j', version: '0.9.6'
}
""".strip(),
            encoding="utf-8",
        )

        analysis = RepositoryAnalyzer().analyze(str(repo))
        report = SCAScanner().scan_repository(analysis.scanner_targets.sca_targets)

        names = {
            dep.get("name")
            for result in report.detailed_results
            for dep in result.vulnerable_dependencies
        }

        assert "io.jsonwebtoken.jjwt-api" in names
        assert "io.jsonwebtoken.jjwt-impl" in names
        assert "org.bitbucket.b_c.jose4j" in names


def test_file_classifier_handles_windows_style_config_paths():
    metadata = FileMetadata(
        file_path="infra\\nginx.conf",
        absolute_path="C:\\repo\\infra\\nginx.conf",
        file_name="nginx.conf",
        extension=".conf",
        language="config",
        category=FileCategory.UNKNOWN,
        size_bytes=128,
    )

    category = FileClassifier().classify(metadata)

    assert category == FileCategory.CONFIGURATION
