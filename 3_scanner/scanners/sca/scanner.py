# scanners/sca/scanner.py
from typing import List, Dict
from models.file_metadata import FileMetadata
from models.scan_result import SCAResult, SCAScanReport
from .parsers import PARSERS
from .vulnerability_db import PQC_VULNERABLE_LIBRARIES
from packaging import version as pkg_version

class SCAScanner:
    """SCA scanner."""
    
    def __init__(self):
        self.vuln_db = PQC_VULNERABLE_LIBRARIES
    
    def scan_file(self, file_metadata: FileMetadata) -> SCAResult:
        """Scan a dependency manifest file."""
        file_name = file_metadata.file_name
        
        # Unsupported dependency manifest
        if file_name not in PARSERS:
            return SCAResult(
                file_path=file_metadata.file_path,
                total_dependencies=0,
                vulnerable_dependencies=[],
                skipped=True,
                skip_reason=f"Unsupported dependency file: {file_name}"
            )
        
        # Parse dependency manifest
        try:
            parser = PARSERS[file_name]
            dependencies = parser.parse(file_metadata.absolute_path)
        except Exception as e:
            return SCAResult(
                file_path=file_metadata.file_path,
                total_dependencies=0,
                vulnerable_dependencies=[],
                skipped=True,
                skip_reason=f"Parse error: {str(e)}"
            )
        
        # Vulnerability checks
        vulnerable_deps = []
        
        for dep in dependencies:
            vuln_info = self._check_vulnerability(dep, file_metadata.language)
            
            if vuln_info:
                vulnerable_deps.append({
                    "name": dep.name,
                    "current_version": dep.version,
                    "dependency_type": dep.dep_type,
                    **vuln_info
                })
        
        return SCAResult(
            file_path=file_metadata.file_path,
            total_dependencies=len(dependencies),
            vulnerable_dependencies=vulnerable_deps,
            total_vulnerabilities=len(vulnerable_deps),
            skipped=False
        )
    
    def _check_vulnerability(self, dep, language: str) -> Dict:
        """Check dependency vulnerability."""
        lang_vulns = self.vuln_db.get(language, {})
        vuln_info = lang_vulns.get(dep.name)
        
        if not vuln_info:
            return None
        
        # All versions vulnerable
        if vuln_info.get("all_versions_vulnerable", False):
            return {
                "severity": "HIGH",
                "reason": vuln_info["reason"],
                "pqc_support": vuln_info["pqc_support"],
                "alternatives": vuln_info.get("alternatives", [])
            }
        
        # Version-specific vulnerabilities
        vulnerable_versions = vuln_info.get("vulnerable_versions", [])
        if self._is_version_vulnerable(dep.version, vulnerable_versions):
            return {
                "severity": "MEDIUM",
                "reason": vuln_info["reason"],
                "pqc_support": vuln_info.get("pqc_support", "none"),
                "pqc_version": vuln_info.get("pqc_version"),
                "alternatives": vuln_info.get("alternatives", [])
            }
        
        return None
    
    def _is_version_vulnerable(self, current_ver: str, vuln_patterns: List[str]) -> bool:
        """Check if version is vulnerable."""
        if current_ver == "unknown":
            return True  # Unknown version: treat as vulnerable
        
        try:
            current = pkg_version.parse(current_ver.strip('<>=~^'))
            
            for pattern in vuln_patterns:
                if pattern.startswith('<'):
                    threshold = pkg_version.parse(pattern[1:])
                    if current < threshold:
                        return True
                elif pattern.startswith('<='):
                    threshold = pkg_version.parse(pattern[2:])
                    if current <= threshold:
                        return True
        except:
            return True  # Parse failure: treat as vulnerable
        
        return False
    
    def scan_repository(
        self, 
        sca_targets: List[FileMetadata]
    ) -> SCAScanReport:
        """Scan a repository."""
        print(f"\nRunning SCA Scanner on {len(sca_targets)} files...")
        
        results = []
        for file_meta in sca_targets:
            print(f"  Scanning: {file_meta.file_path}")
            result = self.scan_file(file_meta)
            results.append(result)
        
        # Aggregate results
        total_deps = sum(r.total_dependencies for r in results if not r.skipped)
        total_vulns = sum(r.total_vulnerabilities for r in results if not r.skipped)
        
        print(f"SCA completed: {total_vulns}/{total_deps} vulnerable dependencies")
        
        return SCAScanReport(
            total_files_scanned=len([r for r in results if not r.skipped]),
            total_dependencies=total_deps,
            total_vulnerable=total_vulns,
            detailed_results=results
        )
