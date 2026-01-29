# language_detector/detector.py
import os
from pathlib import Path
from typing import Optional
from .constants import EXTENSION_LANGUAGE_MAP

class LanguageDetector:
    """언어 감지 클래스"""
    
    def __init__(self):
        self.extension_map = EXTENSION_LANGUAGE_MAP
    
    def detect_language(self, file_path: str) -> str:
        """파일 언어 감지"""
        extension = Path(file_path).suffix.lower()
        
        # 확장자 기반 감지
        if extension in self.extension_map:
            return self.extension_map[extension]
        
        # Shebang 기반 감지 (확장자 없는 경우)
        if not extension:
            shebang_lang = self._detect_by_shebang(file_path)
            if shebang_lang:
                return shebang_lang
        
        return "unknown"
    
    def _detect_by_shebang(self, file_path: str) -> Optional[str]:
        """Shebang 라인으로 언어 감지"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                
                if first_line.startswith('#!'):
                    if 'python' in first_line:
                        return 'python'
                    elif 'node' in first_line or 'javascript' in first_line:
                        return 'javascript'
                    elif 'bash' in first_line or 'sh' in first_line:
                        return 'shell'
                    elif 'ruby' in first_line:
                        return 'ruby'
                    elif 'php' in first_line:
                        return 'php'
        except:
            pass
        
        return None