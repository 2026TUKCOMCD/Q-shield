# scanners/config/scanner.py
import re
import subprocess
from typing import List, Dict
from models.file_metadata import FileMetadata
from models.scan_result import ConfigResult, ConfigScanReport
from .crypto_config_rules import CONFIG_CRYPTO_PATTERNS
import yaml
import xml.etree.ElementTree as ET

class ConfigScanner:
    """설정 파일 스캐너"""
    
    def scan_file(self, file_metadata: FileMetadata) -> ConfigResult:
        """설정 파일 스캔"""
        findings = []
        ext = file_metadata.extension.lower()
        
        # 인증서 파일
        if ext in ['.pem', '.crt', '.cer', '.key']:
            cert_findings = self._analyze_certificate(file_metadata.absolute_path)
            findings.extend(cert_findings)
        
        # YAML/XML 구조화된 설정
        elif ext in ['.yml', '.yaml']:
            yaml_findings = self._scan_yaml(file_metadata.absolute_path)
            findings.extend(yaml_findings)
        
        elif ext == '.xml':
            xml_findings = self._scan_xml(file_metadata.absolute_path)
            findings.extend(xml_findings)
        
        # 텍스트 기반 설정 (.conf, .config, .ini 등)
        else:
            text_findings = self._scan_text_config(file_metadata.absolute_path)
            findings.extend(text_findings)
        
        return ConfigResult(
            file_path=file_metadata.file_path,
            total_findings=len(findings),
            findings=findings,
            skipped=False
        )
    
    def _analyze_certificate(self, cert_path: str) -> List[Dict]:
        """인증서 파일 분석"""
        findings = []
        
        try:
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-text', '-noout'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                cert_text = result.stdout
                
                # RSA 인증서
                if "RSA Public Key" in cert_text or "rsaEncryption" in cert_text:
                    findings.append({
                        "type": "rsa_certificate",
                        "severity": "HIGH",
                        "description": "RSA 기반 인증서 - 양자컴퓨터에 취약",
                        "recommendation": "PQC 안전 인증서로 교체 필요 (예: Dilithium 서명)"
                    })
                
                # ECC/ECDSA 인증서
                elif "EC Public Key" in cert_text or "ecPublicKey" in cert_text:
                    findings.append({
                        "type": "ecc_certificate",
                        "severity": "HIGH",
                        "description": "ECC 기반 인증서 - 양자컴퓨터에 취약",
                        "recommendation": "PQC 안전 인증서로 교체 필요"
                    })
        
        except subprocess.TimeoutExpired:
            findings.append({
                "type": "cert_analysis_timeout",
                "severity": "INFO",
                "description": "인증서 분석 시간 초과"
            })
        except FileNotFoundError:
            # openssl 없음
            pass
        except Exception as e:
            findings.append({
                "type": "cert_parse_error",
                "severity": "INFO",
                "description": f"인증서 분석 실패: {str(e)}"
            })
        
        return findings
    
    def _scan_yaml(self, file_path: str) -> List[Dict]:
        """YAML 파일 스캔"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 텍스트 패턴 매칭도 수행
            findings.extend(self._pattern_match(content))
            
            # YAML 파싱 (구조 확인용)
            try:
                data = yaml.safe_load(content)
                # TODO: 구조화된 데이터에서 암호 설정 찾기
            except:
                pass
        
        except Exception as e:
            findings.append({
                "type": "yaml_parse_error",
                "severity": "INFO",
                "description": f"YAML 파싱 실패: {str(e)}"
            })
        
        return findings
    
    def _scan_xml(self, file_path: str) -> List[Dict]:
        """XML 파일 스캔"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            findings.extend(self._pattern_match(content))
        
        except Exception as e:
            findings.append({
                "type": "xml_parse_error",
                "severity": "INFO",
                "description": f"XML 파싱 실패: {str(e)}"
            })
        
        return findings
    
    def _scan_text_config(self, file_path: str) -> List[Dict]:
        """텍스트 기반 설정 파일 스캔"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            findings.extend(self._pattern_match(content))
        
        except Exception as e:
            findings.append({
                "type": "config_read_error",
                "severity": "INFO",
                "description": f"설정 파일 읽기 실패: {str(e)}"
            })
        
        return findings
    
    def _pattern_match(self, content: str) -> List[Dict]:
        """패턴 매칭"""
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
        """Repository 전체 스캔"""
        print(f"\n⚙️  Running Config Scanner on {len(config_targets)} files...")
        
        results = []
        for file_meta in config_targets:
            print(f"  Scanning: {file_meta.file_path}")
            result = self.scan_file(file_meta)
            results.append(result)
        
        # 결과 집계
        total_findings = sum(r.total_findings for r in results if not r.skipped)
        
        print(f"✅ Config scan completed: {total_findings} findings")
        
        return ConfigScanReport(
            total_files_scanned=len([r for r in results if not r.skipped]),
            total_findings=total_findings,
            detailed_results=results
        )