# scanners/sast/python_analyzer.py
import ast
import re
from typing import List, Dict
from .crypto_rules import CRYPTO_PATTERNS, VULNERABLE_APIS

class PythonASTAnalyzer(ast.NodeVisitor):
    """Python AST-based crypto usage analysis."""
    
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.vulnerabilities = []
        self.imports = []
    
    def analyze(self) -> List[Dict]:
        """Run analysis."""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {self.file_path}: {e}")
        
        return self.vulnerabilities
    
    def visit_Import(self, node: ast.Import):
        """Analyze import statements."""
        for alias in node.names:
            self.imports.append(alias.name)
            
            # Check for vulnerable crypto libraries
            if alias.name in VULNERABLE_APIS["python"]:
                self.vulnerabilities.append({
                    "type": "vulnerable_import",
                    "line": node.lineno,
                    "code": self._get_line(node.lineno),
                    "severity": "MEDIUM",
                    "algorithm": self._get_algorithm_from_import(alias.name),
                    "description": f"PQC-incompatible library import detected: {alias.name}",
                    "recommendation": "Review PQC-safe library replacement."
                })
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Analyze from-import statements."""
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
                        "description": f"PQC-incompatible module import detected: {full_import}",
                        "recommendation": "Review PQC-safe alternatives."
                    })
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Analyze function calls."""
        # RSA.generate(2048) pattern
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
                            "description": "RSA key generation detected - vulnerable to quantum attacks.",
                            "recommendation": "Consider Kyber (KEM) or Dilithium (signatures)."
                        })
        
        self.generic_visit(node)
    
    def _get_line(self, line_num: int) -> str:
        """Return source line text by line number."""
        if 0 < line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1].strip()
        return ""
    
    def _get_algorithm_from_import(self, import_name: str) -> str:
        """Infer algorithm from import name."""
        if "rsa" in import_name.lower():
            return "RSA"
        elif "ec" in import_name.lower() or "ecdsa" in import_name.lower():
            return "ECC/ECDSA"
        return "Unknown"


def analyze_python_file(file_path: str, source_code: str) -> List[Dict]:
    """Analyze Python source using AST and regex patterns."""
    vulnerabilities = []
    
    # 1) AST analysis
    ast_analyzer = PythonASTAnalyzer(file_path, source_code)
    ast_vulnerabilities = ast_analyzer.analyze()
    vulnerabilities.extend(ast_vulnerabilities)
    
    # 2) Regex pattern matching (cases not caught by AST)
    patterns = CRYPTO_PATTERNS.get("python", {})
    
    for rule_name, rule in patterns.items():
        for pattern_str in rule["patterns"]:
            for match in re.finditer(pattern_str, source_code):
                line_num = source_code[:match.start()].count('\n') + 1
                
                # De-duplicate by line number
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
