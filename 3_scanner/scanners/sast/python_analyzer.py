# scanners/sast/python_analyzer.py
import ast
import re
from typing import List, Dict
from .crypto_rules import CRYPTO_PATTERNS, VULNERABLE_APIS

class PythonASTAnalyzer(ast.NodeVisitor):
    """Python AST 기반 암호화 코드 분석"""
    
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.vulnerabilities = []
        self.imports = []
    
    def analyze(self) -> List[Dict]:
        """분석 실행"""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {self.file_path}: {e}")
        
        return self.vulnerabilities
    
    def visit_Import(self, node: ast.Import):
        """import 문 분석"""
        for alias in node.names:
            self.imports.append(alias.name)
            
            # 취약한 라이브러리 임포트 체크
            if alias.name in VULNERABLE_APIS["python"]:
                self.vulnerabilities.append({
                    "type": "vulnerable_import",
                    "line": node.lineno,
                    "code": self._get_line(node.lineno),
                    "severity": "MEDIUM",
                    "algorithm": self._get_algorithm_from_import(alias.name),
                    "description": f"PQC 취약 라이브러리 임포트: {alias.name}",
                    "recommendation": "PQC 안전 라이브러리로 교체 검토"
                })
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from X import Y 분석"""
        if node.module:
            full_imports = [f"{node.module}.{alias.name}" for alias in node.names]
            
            for full_import in full_imports:
                if any(vuln_api in full_import for vuln_api in VULNERABLE_APIS["python"]):
                    self.vulnerabilities.append({
                        "type": "vulnerable_import",
                        "line": node.lineno,
                        "code": self._get_line(node.lineno),
                        "severity": "MEDIUM",
                        "algorithm": self._get_algorithm_from_import(full_import),
                        "description": f"PQC 취약 모듈 임포트: {full_import}",
                        "recommendation": "PQC 안전 대안 검토"
                    })
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """함수 호출 분석"""
        # RSA.generate(2048) 패턴
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "generate":
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "RSA":
                        self.vulnerabilities.append({
                            "type": "rsa_key_generation",
                            "line": node.lineno,
                            "code": self._get_line(node.lineno),
                            "severity": "HIGH",
                            "algorithm": "RSA",
                            "description": "RSA 키 생성 - 양자컴퓨터에 취약",
                            "recommendation": "Kyber(KEM) 또는 Dilithium(서명) 사용 권장"
                        })
        
        self.generic_visit(node)
    
    def _get_line(self, line_num: int) -> str:
        """라인 번호로 코드 가져오기"""
        if 0 < line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1].strip()
        return ""
    
    def _get_algorithm_from_import(self, import_name: str) -> str:
        """임포트 이름에서 알고리즘 추출"""
        if "rsa" in import_name.lower():
            return "RSA"
        elif "ec" in import_name.lower() or "ecdsa" in import_name.lower():
            return "ECC/ECDSA"
        return "Unknown"


def analyze_python_file(file_path: str, source_code: str) -> List[Dict]:
    """Python 파일 분석 (AST + 정규식)"""
    vulnerabilities = []
    
    # 1. AST 분석
    ast_analyzer = PythonASTAnalyzer(file_path, source_code)
    ast_vulnerabilities = ast_analyzer.analyze()
    vulnerabilities.extend(ast_vulnerabilities)
    
    # 2. 정규식 패턴 매칭 (AST로 못 잡은 것들)
    patterns = CRYPTO_PATTERNS.get("python", {})
    
    for rule_name, rule in patterns.items():
        for pattern_str in rule["patterns"]:
            for match in re.finditer(pattern_str, source_code):
                line_num = source_code[:match.start()].count('\n') + 1
                
                # 중복 체크
                if not any(v["line"] == line_num for v in vulnerabilities):
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