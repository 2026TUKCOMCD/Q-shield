# scanners/sca/scanner.py
import re
from typing import List, Dict, Optional
from models.file_metadata import FileMetadata
from models.scan_result import SCAResult, SCAScanReport
from .parsers import PARSERS
from .vulnerability_db import load_pqc_db
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet

class SCAScanner:
    """SCA scanner."""
    
    def __init__(self):
        self.vuln_db = load_pqc_db()
        self.vuln_index = self._build_vuln_index(self.vuln_db)
    
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
                    "scanner_type": "SCA",
                    "rule_id": vuln_info["rule_id"],
                    "library_name": dep.name,
                    "version": dep.version,
                    "severity": vuln_info["severity"],
                    "pqc_classification": vuln_info.get(
                        "pqc_classification",
                        "Traditional Crypto Library",
                    ),
                    "evidence": {
                        "file_path": file_metadata.file_path,
                        "dependency_type": dep.dep_type,
                        "matched_name": vuln_info["matched_name"],
                        "match_type": vuln_info["match_type"],
                        "reason": vuln_info["reason"],
                    },
                    "metadata": {
                        "pqc_support": vuln_info.get("pqc_support"),
                        "pqc_version": vuln_info.get("pqc_version"),
                        "alternatives": vuln_info.get("alternatives", []),
                        "language": self._normalize_language(file_metadata.language),
                    },
                    # Backward compatible fields
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
    
    def _check_vulnerability(self, dep, language: str) -> Optional[Dict]:
        """Check dependency vulnerability."""
        normalized_language = self._normalize_language(language)
        lang_vulns = self.vuln_index.get(normalized_language, [])
        dep_name_raw = dep.name or ""
        dep_norm = self._normalize_dep_name(dep_name_raw)

        vuln_info = None
        matched_name = None
        match_type = None

        # Exact normalized match
        for entry in lang_vulns:
            if entry["norm_key"] == dep_norm:
                vuln_info = entry["info"]
                matched_name = entry["key"]
                match_type = "exact"
                break

        # Exact raw match (case-insensitive)
        if not vuln_info:
            for entry in lang_vulns:
                if entry["key"].lower() == dep_name_raw.lower():
                    vuln_info = entry["info"]
                    matched_name = entry["key"]
                    match_type = "exact"
                    break

        # Partial/contains matching
        if not vuln_info:
            for entry in lang_vulns:
                if self._is_partial_match(dep_norm, entry["norm_key"]):
                    vuln_info = entry["info"]
                    matched_name = entry["key"]
                    match_type = "partial"
                    break

        if not vuln_info:
            return None
        
        # All versions vulnerable
        if vuln_info.get("all_versions_vulnerable", False):
            return {
                "severity": vuln_info.get("severity", "HIGH"),
                "reason": vuln_info["reason"],
                "pqc_support": vuln_info.get("pqc_support"),
                "pqc_classification": vuln_info.get(
                    "pqc_classification",
                    "Traditional Crypto Library",
                ),
                "alternatives": vuln_info.get("alternatives", []),
                "rule_id": self._normalize_dep_name(matched_name),
                "matched_name": matched_name,
                "match_type": match_type,
            }
        
        # Version-specific vulnerabilities
        vulnerable_versions = vuln_info.get("vulnerable_versions", [])
        if self._is_version_vulnerable(dep.version, vulnerable_versions):
            return {
                "severity": vuln_info.get("severity", "MEDIUM"),
                "reason": vuln_info["reason"],
                "pqc_support": vuln_info.get("pqc_support", "none"),
                "pqc_classification": vuln_info.get(
                    "pqc_classification",
                    "Traditional Crypto Library",
                ),
                "pqc_version": vuln_info.get("pqc_version"),
                "alternatives": vuln_info.get("alternatives", []),
                "rule_id": self._normalize_dep_name(matched_name),
                "matched_name": matched_name,
                "match_type": match_type,
            }
        
        return None
    
    def _is_version_vulnerable(self, current_ver: str, vuln_patterns: List[str]) -> bool:
        """Check if version is vulnerable."""
        if not vuln_patterns:
            return False
        if not current_ver or current_ver == "unknown":
            return True  # Unknown version: treat as vulnerable

        current = self._normalize_version(current_ver)
        if current is None:
            return True  # Parse failure: treat as vulnerable

        try:
            for pattern in vuln_patterns:
                spec = SpecifierSet(pattern)
                if spec.contains(str(current), prereleases=True):
                    return True
        except Exception:
            # Fallback: manual compare for < and <=
            try:
                for pattern in vuln_patterns:
                    pattern = pattern.strip()
                    if pattern.startswith("<="):
                        threshold = pkg_version.parse(pattern[2:])
                        if current <= threshold:
                            return True
                    elif pattern.startswith("<"):
                        threshold = pkg_version.parse(pattern[1:])
                        if current < threshold:
                            return True
                    elif pattern.startswith(">="):
                        threshold = pkg_version.parse(pattern[2:])
                        if current >= threshold:
                            return True
                    elif pattern.startswith(">"):
                        threshold = pkg_version.parse(pattern[1:])
                        if current > threshold:
                            return True
                    elif pattern.startswith("=="):
                        threshold = pkg_version.parse(pattern[2:])
                        if current == threshold:
                            return True
            except Exception:
                return True
        return False

    def _normalize_language(self, language: str) -> str:
        lang = (language or "").strip().lower()
        lang_map = {
            "js": "javascript",
            "node": "javascript",
            "nodejs": "javascript",
            "typescript": "javascript",
            "ts": "javascript",
            "py": "python",
        }
        return lang_map.get(lang, lang)

    def _normalize_dep_name(self, name: str) -> str:
        raw = (name or "").strip().lower()
        if raw.startswith("@") and "/" in raw:
            raw = raw.split("/", 1)[1]
        raw = raw.replace("\\", "/")
        raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
        for prefix in ("python", "py", "node", "js", "java", "lib"):
            if raw.startswith(f"{prefix}-"):
                raw = raw[len(prefix) + 1 :]
        return raw

    def _is_partial_match(self, dep_norm: str, vuln_norm: str) -> bool:
        if not dep_norm or not vuln_norm:
            return False
        if dep_norm == vuln_norm:
            return True
        if len(dep_norm) < 4 or len(vuln_norm) < 4:
            return False
        return dep_norm in vuln_norm or vuln_norm in dep_norm

    def _normalize_version(self, version_str: str) -> Optional[pkg_version.Version]:
        if not version_str:
            return None
        match = re.search(r"\d+(\.\d+){0,3}", version_str)
        if not match:
            return None
        try:
            return pkg_version.parse(match.group(0))
        except Exception:
            return None

    def _build_vuln_index(self, vuln_db: Dict) -> Dict[str, List[Dict]]:
        index: Dict[str, List[Dict]] = {}
        for language, entries in vuln_db.items():
            normalized_language = self._normalize_language(language)
            index[normalized_language] = []
            for key, info in entries.items():
                index[normalized_language].append(
                    {
                        "key": key,
                        "norm_key": self._normalize_dep_name(key),
                        "info": info,
                    }
                )
        return index
    
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
