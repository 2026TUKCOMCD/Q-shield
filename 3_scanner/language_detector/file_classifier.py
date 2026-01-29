# language_detector/file_classifier.py
import os
from pathlib import Path
from models.file_metadata import FileMetadata, FileCategory
from .constants import (
    SOURCE_CODE_EXTENSIONS, CONFIG_PATHS, 
    DEPENDENCY_FILES
)

class FileClassifier:
    """파일 카테고리 분류"""
    
    def classify(self, metadata: FileMetadata) -> FileCategory:
        """파일 카테고리 결정"""
        path_lower = metadata.file_path.lower()
        ext = metadata.extension.lower()
        filename = metadata.file_name
        
        # 1. 의존성 파일
        if filename in DEPENDENCY_FILES:
            return FileCategory.DEPENDENCY_MANIFEST
        
        # 2. 설정 파일
        if self._is_config_file(path_lower, ext):
            return FileCategory.CONFIGURATION
        
        # 3. 소스 코드
        if ext in SOURCE_CODE_EXTENSIONS:
            return FileCategory.SOURCE_CODE
        
        # 4. 바이너리
        if metadata.is_binary:
            return FileCategory.BINARY
        
        # 5. 문서
        if ext in ['.md', '.txt', '.rst', '.doc', '.docx']:
            return FileCategory.DOCUMENTATION
        
        return FileCategory.UNKNOWN
    
    def _is_config_file(self, path: str, ext: str) -> bool:
        """설정 파일 여부 확인"""
        # 경로에 config 관련 키워드 포함
        for config_path in CONFIG_PATHS:
            if config_path in path:
                return True
        
        # 설정 파일 확장자
        config_extensions = ['.yml', '.yaml', '.xml', '.toml', 
                           '.ini', '.conf', '.config', '.env']
        if ext in config_extensions:
            return True
        
        # 인증서 파일
        if ext in ['.pem', '.crt', '.cer', '.key']:
            return True
        
        # 특정 파일명
        config_files = ['dockerfile', 'docker-compose.yml', 
                       'nginx.conf', 'apache.conf']
        if path.split('/')[-1].lower() in config_files:
            return True
        
        return False