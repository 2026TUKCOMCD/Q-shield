# scanners/config/scanner.py
import re
import subprocess
from typing import List, Dict, Optional
from models.file_metadata import FileMetadata
from models.scan_result import ConfigResult, ConfigScanReport
from .crypto_config_rules import CONFIG_CRYPTO_PATTERNS
import yaml
import xml.etree.ElementTree as ET

class ConfigScanner:
    """Config scanner."""
    _PEM_READ_BYTES = 4096
    _ENCRYPTED_MARKERS = (
        "BEGIN ENCRYPTED PRIVATE KEY",
        "BEGIN RSA PRIVATE KEY",
        "BEGIN EC PRIVATE KEY",
        "BEGIN PRIVATE KEY",
        "Proc-Type: 4,ENCRYPTED",
        "DEK-Info:",
    )
    _CERT_MARKER = "BEGIN CERTIFICATE"
    
    def scan_file(self, file_metadata: FileMetadata) -> ConfigResult:
        """Scan a config file."""
        findings = []
        ext = file_metadata.extension.lower()
        
        # Certificate files
        if ext in ['.pem', '.crt', '.cer', '.key']:
            cert_findings = self._analyze_certificate(
                file_metadata.absolute_path,
                ext=ext,
            )
            findings.extend(cert_findings)
        
        # YAML/XML structured config
        elif ext in ['.yml', '.yaml']:
            yaml_findings = self._scan_yaml(file_metadata.absolute_path)
            findings.extend(yaml_findings)
        
        elif ext == '.xml':
            xml_findings = self._scan_xml(file_metadata.absolute_path)
            findings.extend(xml_findings)
        
        # Text config (.conf, .config, .ini, etc.)
        else:
            text_findings = self._scan_text_config(file_metadata.absolute_path)
            findings.extend(text_findings)
        
        return ConfigResult(
            file_path=file_metadata.file_path,
            total_findings=len(findings),
            findings=findings,
            skipped=False
        )
    
    def _analyze_certificate(self, cert_path: str, ext: str) -> List[Dict]:
        """Analyze certificate file."""
        findings = []

        # Avoid OpenSSL prompts: skip encrypted/private keys and non-certs.
        skip_reason = self._should_skip_cert_file(cert_path, ext)
        if skip_reason:
            findings.append({
                "type": "cert_skipped",
                "severity": "INFO",
                "description": "Certificate analysis skipped.",
                "meta": {
                    "skip_reason": skip_reason
                }
            })
            return findings

        try:
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-text', '-noout'],
                capture_output=True,
                text=True,
                timeout=5,
                stdin=subprocess.DEVNULL,
            )
            
            if result.returncode == 0:
                cert_text = result.stdout
                
                # RSA certificate
                if "RSA Public Key" in cert_text or "rsaEncryption" in cert_text:
                    findings.append({
                        "type": "rsa_certificate",
                        "severity": "HIGH",
                        "description": "RSA certificate detected - vulnerable to quantum attacks.",
                        "recommendation": "Replace with PQC-safe certificate (e.g., Dilithium signatures)."
                    })
                
                # ECC/ECDSA certificate
                elif "EC Public Key" in cert_text or "ecPublicKey" in cert_text:
                    findings.append({
                        "type": "ecc_certificate",
                        "severity": "HIGH",
                        "description": "ECC certificate detected - vulnerable to quantum attacks.",
                        "recommendation": "Replace with PQC-safe certificate."
                    })
            else:
                findings.append({
                    "type": "cert_skipped",
                    "severity": "INFO",
                    "description": "OpenSSL could not parse certificate.",
                    "meta": {
                        "skip_reason": "openssl_parse_failed"
                    }
                })
        
        except subprocess.TimeoutExpired:
            findings.append({
                "type": "cert_skipped",
                "severity": "INFO",
                "description": "Certificate analysis timed out.",
                "meta": {
                    "skip_reason": "openssl_timeout"
                }
            })
        except FileNotFoundError:
            findings.append({
                "type": "cert_skipped",
                "severity": "INFO",
                "description": "OpenSSL not available; skipping certificate analysis.",
                "meta": {
                    "skip_reason": "openssl_not_available"
                }
            })
        except Exception as e:
            findings.append({
                "type": "cert_skipped",
                "severity": "INFO",
                "description": f"Certificate analysis failed: {str(e)}",
                "meta": {
                    "skip_reason": "openssl_error"
                }
            })
        
        return findings

    def _should_skip_cert_file(self, cert_path: str, ext: str) -> Optional[str]:
        if ext == ".key":
            return "private_key_file"

        header = self._peek_pem_header(cert_path)
        if header is None:
            return "cert_read_failed"

        header_upper = header.upper()
        for marker in self._ENCRYPTED_MARKERS:
            if marker in header_upper:
                return "encrypted_private_key_requires_passphrase"

        if ext == ".pem":
            if self._CERT_MARKER not in header_upper:
                return "pem_not_certificate"

        return None

    def _peek_pem_header(self, cert_path: str) -> Optional[str]:
        try:
            with open(cert_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(self._PEM_READ_BYTES)
        except Exception:
            return None
    
    def _scan_yaml(self, file_path: str) -> List[Dict]:
        """Scan YAML config."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Regex pattern matching
            findings.extend(self._pattern_match(content))
            
            # YAML parsing (structured scan)
            try:
                data = yaml.safe_load(content)
                # TODO: Extract crypto-related settings from structured YAML
            except:
                pass
        
        except Exception as e:
            findings.append({
                "type": "yaml_parse_error",
                "severity": "INFO",
                "description": f"YAML parse failed: {str(e)}"
            })
        
        return findings
    
    def _scan_xml(self, file_path: str) -> List[Dict]:
        """Scan XML config."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            findings.extend(self._pattern_match(content))
        
        except Exception as e:
            findings.append({
                "type": "xml_parse_error",
                "severity": "INFO",
                "description": f"XML parse failed: {str(e)}"
            })
        
        return findings
    
    def _scan_text_config(self, file_path: str) -> List[Dict]:
        """Scan text config."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            findings.extend(self._pattern_match(content))
        
        except Exception as e:
            findings.append({
                "type": "config_read_error",
                "severity": "INFO",
                "description": f"Config read failed: {str(e)}"
            })
        
        return findings
    
    def _pattern_match(self, content: str) -> List[Dict]:
        """Apply regex pattern matching."""
        findings = []
        
        for rule_name, rule in CONFIG_CRYPTO_PATTERNS.items():
            for pattern_str in rule["patterns"]:
                for match in re.finditer(pattern_str, content, re.IGNORECASE):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    findings.append({
                        "type": rule_name,
                        "line": line_num,
                        "matched_text": match.group(0),
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "recommendation": rule["recommendation"]
                    })
        
        return findings
    
    def scan_repository(
        self, 
        config_targets: List[FileMetadata]
    ) -> ConfigScanReport:
        """Scan a repository."""
        print(f"\nRunning Config Scanner on {len(config_targets)} files...")
        
        results = []
        for file_meta in config_targets:
            print(f"  Scanning: {file_meta.file_path}")
            result = self.scan_file(file_meta)
            results.append(result)
        
        # Aggregate results
        total_findings = sum(r.total_findings for r in results if not r.skipped)
        
        print(f"Config scan completed: {total_findings} findings")
        
        return ConfigScanReport(
            total_files_scanned=len([r for r in results if not r.skipped]),
            total_findings=total_findings,
            detailed_results=results
        )
