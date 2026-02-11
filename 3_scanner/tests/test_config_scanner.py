from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.file_metadata import FileMetadata, FileCategory
from scanners.config.scanner import ConfigScanner


def _fixture_root() -> Path:
    return ROOT / "tests" / "fixtures" / "config_project"


def _make_metadata(path: Path, file_path: str) -> FileMetadata:
    return FileMetadata(
        file_path=file_path,
        absolute_path=str(path),
        file_name=path.name,
        extension=path.suffix,
        language="config",
        category=FileCategory.CONFIGURATION,
        size_bytes=path.stat().st_size,
        line_count=0,
        encoding="utf-8",
        is_binary=False,
    )


def test_config_scanner_detects_tls_issues():
    fixture_root = _fixture_root()
    nginx_path = fixture_root / "nginx.conf"
    metadata = _make_metadata(nginx_path, "nginx.conf")
    report = ConfigScanner().scan_repository([metadata])

    types = set()
    for result in report.detailed_results:
        for finding in result.findings:
            types.add(finding.get("type"))

    assert "outdated_tls" in types
    assert "rsa_cipher" in types
    assert "ecdsa_cipher" in types


def test_config_scanner_skips_encrypted_private_key(monkeypatch):
    fixture_root = _fixture_root()
    key_path = fixture_root / "encrypted_private_key.pem"

    def _fail_run(*args, **kwargs):
        raise AssertionError("OpenSSL should not be invoked for encrypted keys")

    monkeypatch.setattr(subprocess, "run", _fail_run)

    metadata = _make_metadata(key_path, "encrypted_private_key.pem")
    result = ConfigScanner().scan_file(metadata)

    assert any(
        f.get("type") == "cert_skipped"
        and f.get("meta", {}).get("skip_reason") == "encrypted_private_key_requires_passphrase"
        for f in result.findings
    )


def test_config_scanner_analyzes_certificate_non_interactive(monkeypatch):
    fixture_root = _fixture_root()
    cert_path = fixture_root / "cert.pem"

    def _mock_run(*args, **kwargs):
        assert kwargs.get("stdin") is subprocess.DEVNULL
        assert kwargs.get("timeout") == 5
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="RSA Public Key",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _mock_run)

    metadata = _make_metadata(cert_path, "cert.pem")
    result = ConfigScanner().scan_file(metadata)

    assert any(f.get("type") == "rsa_certificate" for f in result.findings)


def test_config_scanner_many_pems_finishes(tmp_path, monkeypatch):
    def _mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="RSA Public Key",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _mock_run)

    pem_content = (
        "-----BEGIN CERTIFICATE-----\n"
        "MIIB...\n"
        "-----END CERTIFICATE-----\n"
    )

    metas = []
    for idx in range(50):
        pem_path = tmp_path / f"cert_{idx}.pem"
        pem_path.write_text(pem_content, encoding="utf-8")
        metas.append(_make_metadata(pem_path, f"cert_{idx}.pem"))

    report = ConfigScanner().scan_repository(metas)
    assert report.total_files_scanned == 50
