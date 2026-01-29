# models/file_metadata.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class FileCategory(Enum):
    """파일 카테고리"""
    SOURCE_CODE = "source_code"
    CONFIGURATION = "configuration"
    DEPENDENCY_MANIFEST = "dependency_manifest"
    DOCUMENTATION = "documentation"
    BINARY = "binary"
    UNKNOWN = "unknown"

@dataclass
class FileMetadata:
    """파일 메타데이터"""
    file_path: str                    # 상대 경로
    absolute_path: str                # 절대 경로
    file_name: str                    # 파일명
    extension: str                    # 확장자
    language: str                     # 감지된 언어
    category: FileCategory            # 파일 카테고리
    size_bytes: int                   # 파일 크기
    line_count: int = 0               # 코드 라인 수
    encoding: str = "utf-8"           # 인코딩
    is_binary: bool = False           # 바이너리 여부
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class LanguageStats:
    """언어별 통계"""
    language: str
    file_count: int
    total_lines: int
    total_bytes: int
    percentage: float

@dataclass
class ScannerTargets:
    """스캐너별 처리 대상"""
    sast_targets: list[FileMetadata]      # SAST용 소스 파일
    sca_targets: list[FileMetadata]       # SCA용 의존성 파일
    config_targets: list[FileMetadata]    # Config용 설정 파일

@dataclass
class RepositoryAnalysis:
    """Repository 분석 결과"""
    repository_path: str
    total_files: int
    file_metadata_list: list[FileMetadata]
    language_stats: list[LanguageStats]
    scanner_targets: ScannerTargets
    analyzed_at: datetime = field(default_factory=datetime.now)