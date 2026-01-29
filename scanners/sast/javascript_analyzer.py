# scanners/sast/javascript_analyzer.py
import re
from typing import List, Dict
from .crypto_rules import CRYPTO_PATTERNS

def analyze_javascript_file(file_path: str, source_code: str) -> List[Dict]:
    """JavaScript/TypeScript 파일 분석 (정규식 기반)"""
    vulnerabilities = []
    patterns = CRYPTO_PATTERNS.get("javascript", {})
    
    for rule_name, rule in patterns.items():
        for pattern_str in rule["patterns"]:
            for match in re.finditer(pattern_str, source_code, re.MULTILINE):
                line_num = source_code[:match.start()].count('\n') + 1
                
                vulnerabilities.append({
                    "type": rule_name,
                    "line": line_num,
                    "code": match.group(0),
                    "severity": rule["severity"],
                    "algorithm": rule["algorithm"],
                    "description": rule["description"],
                    "recommendation": rule["recommendation"]
                })
    
    return vulnerabilities