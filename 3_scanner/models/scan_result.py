# models/scan_result.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class SASTResult:
    """SAST 스캔 결과 (파일별)"""
    file_path: str
    language: str
    vulnerabilities: List[Dict]
    total_issues: int = 0
    skipped: bool = False
    skip_reason: str = ""

@dataclass
class SASTScanReport:
    """SAST 전체 리포트"""
    total_files_scanned: int
    total_vulnerabilities: int
    severity_breakdown: Dict[str, int]
    algorithm_breakdown: Dict[str, int]
    detailed_results: List[SASTResult]
    scanned_at: datetime = field(default_factory=datetime.now)

@dataclass
class SCAResult:
    """SCA 스캔 결과 (파일별)"""
    file_path: str
    total_dependencies: int
    vulnerable_dependencies: List[Dict]
    total_vulnerabilities: int = 0
    skipped: bool = False
    skip_reason: str = ""

@dataclass
class SCAScanReport:
    """SCA 전체 리포트"""
    total_files_scanned: int
    total_dependencies: int
    total_vulnerable: int
    detailed_results: List[SCAResult]
    scanned_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConfigResult:
    """Config 스캔 결과 (파일별)"""
    file_path: str
    total_findings: int
    findings: List[Dict]
    skipped: bool = False
    skip_reason: str = ""

@dataclass
class ConfigScanReport:
    """Config 전체 리포트"""
    total_files_scanned: int
    total_findings: int
    detailed_results: List[ConfigResult]
    scanned_at: datetime = field(default_factory=datetime.now)

@dataclass
class CompleteScanResult:
    """최종 통합 결과"""
    repository_url: str
    repository_path: str
    language_analysis: dict  # RepositoryAnalysis를 dict로 변환
    sast_report: dict
    sca_report: dict
    config_report: dict
    total_issues: int
    scanned_at: datetime = field(default_factory=datetime.now)