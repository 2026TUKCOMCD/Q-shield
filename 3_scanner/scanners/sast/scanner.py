# scanners/sast/scanner.py
from typing import List, Dict
from models.file_metadata import FileMetadata
from models.scan_result import SASTResult, SASTScanReport
from .python_analyzer import analyze_python_file
from .javascript_analyzer import analyze_javascript_file
from .java_analyzer import analyze_java_file

class SASTScanner:
    """SAST 스캐너 메인 클래스"""
    
    def __init__(self):
        self.analyzers = {
            "python": analyze_python_file,
            "javascript": analyze_javascript_file,
            "typescript": analyze_javascript_file,  # JS와 동일
            "java": analyze_java_file,
            # 추가 언어...
        }
    
    def scan_file(self, file_metadata: FileMetadata) -> SASTResult:
        """개별 파일 스캔"""
        language = file_metadata.language.lower()
        
        # 지원하지 않는 언어
        if language not in self.analyzers:
            return SASTResult(
                file_path=file_metadata.file_path,
                language=language,
                vulnerabilities=[],
                skipped=True,
                skip_reason=f"Unsupported language: {language}"
            )
        
        # 파일 읽기
        try:
            with open(file_metadata.absolute_path, 'r', 
                     encoding=file_metadata.encoding, errors='ignore') as f:
                source_code = f.read()
        except Exception as e:
            return SASTResult(
                file_path=file_metadata.file_path,
                language=language,
                vulnerabilities=[],
                skipped=True,
                skip_reason=f"Read error: {str(e)}"
            )
        
        # 분석 실행
        analyzer = self.analyzers[language]
        vulnerabilities = analyzer(file_metadata.absolute_path, source_code)
        
        return SASTResult(
            file_path=file_metadata.file_path,
            language=language,
            vulnerabilities=vulnerabilities,
            total_issues=len(vulnerabilities),
            skipped=False
        )
    
    def scan_repository(
        self, 
        sast_targets: List[FileMetadata]
    ) -> SASTScanReport:
        """Repository 전체 스캔"""
        print(f"\n🔍 Running SAST Scanner on {len(sast_targets)} files...")
        
        results = []
        for file_meta in sast_targets:
            print(f"  Scanning: {file_meta.file_path}")
            result = self.scan_file(file_meta)
            results.append(result)
        
        # 결과 집계
        total_vulnerabilities = sum(r.total_issues for r in results if not r.skipped)
        
        severity_count = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        algorithm_count = {}
        
        for result in results:
            if result.skipped:
                continue
            
            for vuln in result.vulnerabilities:
                severity = vuln.get("severity", "MEDIUM")
                severity_count[severity] = severity_count.get(severity, 0) + 1
                
                algo = vuln.get("algorithm", "Unknown")
                algorithm_count[algo] = algorithm_count.get(algo, 0) + 1
        
        print(f"✅ SAST completed: {total_vulnerabilities} vulnerabilities found")
        
        return SASTScanReport(
            total_files_scanned=len([r for r in results if not r.skipped]),
            total_vulnerabilities=total_vulnerabilities,
            severity_breakdown=severity_count,
            algorithm_breakdown=algorithm_count,
            detailed_results=results
        )