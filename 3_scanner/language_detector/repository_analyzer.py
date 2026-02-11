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
from .constants import IGNORE_DIRECTORIES, IGNORE_FILE_PATTERNS, DEPENDENCY_LANGUAGE_MAP

class RepositoryAnalyzer:
    """Analyze repository files and select scanner targets."""
    
    def __init__(self):
        self.detector = LanguageDetector()
        self.classifier = FileClassifier()
    
    def analyze(self, repo_path: str) -> RepositoryAnalysis:
        """Run repository analysis."""
        print(f"Analyzing repository: {repo_path}")
        
        # 1) Collect all files
        all_files = self._collect_files(repo_path)
        print(f"Found {len(all_files)} files")
        
        # 2) Analyze each file
        file_metadata_list = []
        for file_path in all_files:
            metadata = self._analyze_file(file_path, repo_path)
            if metadata:
                file_metadata_list.append(metadata)
        
        print(f"Analyzed {len(file_metadata_list)} files")
        
        # 3) Build language statistics
        language_stats = self._generate_language_stats(file_metadata_list)
        
        # 4) Classify scanner targets
        scanner_targets = self._classify_for_scanners(file_metadata_list)
        
        print(f"SAST targets: {len(scanner_targets.sast_targets)}")
        print(f"SCA targets: {len(scanner_targets.sca_targets)}")
        print(f"Config targets: {len(scanner_targets.config_targets)}")
        
        return RepositoryAnalysis(
            repository_path=repo_path,
            total_files=len(file_metadata_list),
            file_metadata_list=file_metadata_list,
            language_stats=language_stats,
            scanner_targets=scanner_targets
        )
    
    def _collect_files(self, repo_path: str) -> List[str]:
        """Collect all files under the repository root."""
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRECTORIES]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Skip ignored file patterns
                if self._should_ignore_file(filename):
                    continue
                
                files.append(file_path)
        
        return files
    
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if a file should be ignored."""
        for pattern in IGNORE_FILE_PATTERNS:
            if re.match(pattern, filename):
                return True
        return False
    
    def _analyze_file(
        self,
        file_path: str,
        repo_path: str,
    ) -> FileMetadata:
        """Analyze a single file and return metadata."""
        try:
            stat = os.stat(file_path)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Binary check
            is_binary = self._is_binary(file_path)
            
            # Line count for text files only
            line_count = 0
            encoding = 'utf-8'
            if not is_binary:
                line_count, encoding = self._count_lines(file_path)
            
            # Language detection
            language = self.detector.detect_language(file_path)
            
            # Build metadata
            metadata = FileMetadata(
                file_path=rel_path,
                absolute_path=file_path,
                file_name=os.path.basename(file_path),
                extension=Path(file_path).suffix,
                language=language,
                category=FileCategory.UNKNOWN,  # Will be classified later
                size_bytes=stat.st_size,
                line_count=line_count,
                encoding=encoding,
                is_binary=is_binary
            )
            
            # Category classification
            metadata.category = self.classifier.classify(metadata)
            # Dependency manifests: override language for SCA
            if metadata.category == FileCategory.DEPENDENCY_MANIFEST:
                dep_lang = DEPENDENCY_LANGUAGE_MAP.get(metadata.file_name)
                if dep_lang:
                    metadata.language = dep_lang

            
            return metadata
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _is_binary(self, file_path: str) -> bool:
        """Check if a file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return False
    
    def _count_lines(self, file_path: str) -> tuple[int, str]:
        """Count lines and detect encoding."""
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
        file_metadata_list: List[FileMetadata],
    ) -> List[LanguageStats]:
        """Generate language statistics."""
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
        
        # Total bytes
        total_bytes = sum(s['bytes'] for s in stats_dict.values())
        
        # Build LanguageStats list
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
        
        # Sort by percentage descending
        stats_list.sort(key=lambda x: x.percentage, reverse=True)
        
        return stats_list
    
    def _classify_for_scanners(
        self,
        file_metadata_list: List[FileMetadata],
    ) -> ScannerTargets:
        """Classify files for each scanner."""
        sast_targets = []
        sca_targets = []
        config_targets = []
        
        for metadata in file_metadata_list:
            if metadata.category == FileCategory.SOURCE_CODE:
                # Source code files -> SAST
                sast_targets.append(metadata)
            
            elif metadata.category == FileCategory.DEPENDENCY_MANIFEST:
                # Dependency manifests -> SCA
                sca_targets.append(metadata)
            
            elif metadata.category == FileCategory.CONFIGURATION:
                # Config files -> Config scanner (crypto-related only)
                if self._is_crypto_related_config(metadata):
                    config_targets.append(metadata)
        
        return ScannerTargets(
            sast_targets=sast_targets,
            sca_targets=sca_targets,
            config_targets=config_targets
        )
    
    def _is_crypto_related_config(self, metadata: FileMetadata) -> bool:
        """Check if a config file is crypto-related."""
        # Certificate files
        if metadata.extension in ['.pem', '.crt', '.cer', '.key']:
            return True
        
        # TLS/SSL-related configs
        crypto_keywords = ['ssl', 'tls', 'cert', 'key', 'crypto', 'nginx', 'apache']
        path_lower = metadata.file_path.lower()
        
        return any(keyword in path_lower for keyword in crypto_keywords)
