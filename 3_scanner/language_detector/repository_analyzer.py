# language_detector/repository_analyzer.py
import os
import re
from pathlib import Path
from typing import List
from models.file_metadata import (
    FileMetadata, LanguageStats, ScannerTargets, 
    RepositoryAnalysis, FileCategory
)
from .detector import LanguageDetector
from .file_classifier import FileClassifier
from .constants import IGNORE_DIRECTORIES, IGNORE_FILE_PATTERNS

class RepositoryAnalyzer:
    """Repository 전체 분석"""
    
    def __init__(self):
        self.detector = LanguageDetector()
        self.classifier = FileClassifier()
    
    def analyze(self, repo_path: str) -> RepositoryAnalysis:
        """Repository 분석 메인"""
        print(f"🔍 Analyzing repository: {repo_path}")
        
        # 1. 모든 파일 수집
        all_files = self._collect_files(repo_path)
        print(f"📁 Found {len(all_files)} files")
        
        # 2. 각 파일 분석
        file_metadata_list = []
        for file_path in all_files:
            metadata = self._analyze_file(file_path, repo_path)
            if metadata:
                file_metadata_list.append(metadata)
        
        print(f"✅ Analyzed {len(file_metadata_list)} files")
        
        # 3. 언어별 통계 생성
        language_stats = self._generate_language_stats(file_metadata_list)
        
        # 4. 스캐너별 분류
        scanner_targets = self._classify_for_scanners(file_metadata_list)
        
        print(f"🎯 SAST targets: {len(scanner_targets.sast_targets)}")
        print(f"🎯 SCA targets: {len(scanner_targets.sca_targets)}")
        print(f"🎯 Config targets: {len(scanner_targets.config_targets)}")
        
        return RepositoryAnalysis(
            repository_path=repo_path,
            total_files=len(file_metadata_list),
            file_metadata_list=file_metadata_list,
            language_stats=language_stats,
            scanner_targets=scanner_targets
        )
    
    def _collect_files(self, repo_path: str) -> List[str]:
        """모든 파일 수집"""
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # 무시할 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRECTORIES]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # 무시할 파일 패턴 체크
                if self._should_ignore_file(filename):
                    continue
                
                files.append(file_path)
        
        return files
    
    def _should_ignore_file(self, filename: str) -> bool:
        """파일 무시 여부"""
        for pattern in IGNORE_FILE_PATTERNS:
            if re.match(pattern, filename):
                return True
        return False
    
    def _analyze_file(
        self, 
        file_path: str, 
        repo_path: str
    ) -> FileMetadata:
        """개별 파일 분석"""
        try:
            stat = os.stat(file_path)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # 바이너리 체크
            is_binary = self._is_binary(file_path)
            
            # 라인 수 계산 (텍스트 파일만)
            line_count = 0
            encoding = 'utf-8'
            if not is_binary:
                line_count, encoding = self._count_lines(file_path)
            
            # 언어 감지
            language = self.detector.detect_language(file_path)
            
            # 메타데이터 생성
            metadata = FileMetadata(
                file_path=rel_path,
                absolute_path=file_path,
                file_name=os.path.basename(file_path),
                extension=Path(file_path).suffix,
                language=language,
                category=FileCategory.UNKNOWN,  # 나중에 분류
                size_bytes=stat.st_size,
                line_count=line_count,
                encoding=encoding,
                is_binary=is_binary
            )
            
            # 카테고리 분류
            metadata.category = self.classifier.classify(metadata)
            
            return metadata
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
            return None
    
    def _is_binary(self, file_path: str) -> bool:
        """바이너리 파일 체크"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return False
    
    def _count_lines(self, file_path: str) -> tuple[int, str]:
        """라인 수 계산 및 인코딩 감지"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = sum(1 for _ in f)
                return lines, encoding
            except:
                continue
        
        return 0, 'unknown'
    
    def _generate_language_stats(
        self, 
        file_metadata_list: List[FileMetadata]
    ) -> List[LanguageStats]:
        """언어별 통계 생성"""
        stats_dict = {}
        
        for metadata in file_metadata_list:
            lang = metadata.language
            if lang not in stats_dict:
                stats_dict[lang] = {
                    'count': 0,
                    'lines': 0,
                    'bytes': 0
                }
            
            stats_dict[lang]['count'] += 1
            stats_dict[lang]['lines'] += metadata.line_count
            stats_dict[lang]['bytes'] += metadata.size_bytes
        
        # 총 바이트 계산
        total_bytes = sum(s['bytes'] for s in stats_dict.values())
        
        # LanguageStats 객체 생성
        stats_list = []
        for lang, data in stats_dict.items():
            percentage = (data['bytes'] / total_bytes * 100) if total_bytes > 0 else 0
            
            stats_list.append(LanguageStats(
                language=lang,
                file_count=data['count'],
                total_lines=data['lines'],
                total_bytes=data['bytes'],
                percentage=round(percentage, 2)
            ))
        
        # 퍼센티지 내림차순 정렬
        stats_list.sort(key=lambda x: x.percentage, reverse=True)
        
        return stats_list
    
    def _classify_for_scanners(
        self, 
        file_metadata_list: List[FileMetadata]
    ) -> ScannerTargets:
        """스캐너별 대상 분류"""
        sast_targets = []
        sca_targets = []
        config_targets = []
        
        for metadata in file_metadata_list:
            if metadata.category == FileCategory.SOURCE_CODE:
                # 소스 코드 → SAST
                sast_targets.append(metadata)
            
            elif metadata.category == FileCategory.DEPENDENCY_MANIFEST:
                # 의존성 파일 → SCA
                sca_targets.append(metadata)
            
            elif metadata.category == FileCategory.CONFIGURATION:
                # 설정 파일 → Config (암호 관련만)
                if self._is_crypto_related_config(metadata):
                    config_targets.append(metadata)
        
        return ScannerTargets(
            sast_targets=sast_targets,
            sca_targets=sca_targets,
            config_targets=config_targets
        )
    
    def _is_crypto_related_config(self, metadata: FileMetadata) -> bool:
        """암호 관련 설정 파일인지 확인"""
        # 인증서 파일
        if metadata.extension in ['.pem', '.crt', '.cer', '.key']:
            return True
        
        # TLS/SSL 관련 설정
        crypto_keywords = ['ssl', 'tls', 'cert', 'key', 'crypto', 'nginx', 'apache']
        path_lower = metadata.file_path.lower()
        
        return any(keyword in path_lower for keyword in crypto_keywords)