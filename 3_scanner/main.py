# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil
import os

from language_detector.repository_analyzer import RepositoryAnalyzer
from scanners.sast.scanner import SASTScanner
from scanners.sca.scanner import SCAScanner
from scanners.config.scanner import ConfigScanner
from utils.git_utils import clone_repository
from models.scan_result import CompleteScanResult

app = FastAPI(title="PQC Scanner API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    github_url: str

class ScanResponse(BaseModel):
    status: str
    message: str
    result: Optional[dict] = None

@app.post("/api/scan", response_model=ScanResponse)
async def scan_repository(request: ScanRequest):
    """
    Repository 스캔 메인 엔드포인트
    """
    github_url = request.github_url
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting PQC scan for: {github_url}")
    print(f"{'='*60}\n")
    
    repo_path = None
    should_cleanup = False  # 스캔 후 폴더 삭제 여부를 결정하는 플래그
    
    try:
        # 1. 로컬 경로인지 확인하거나 Repository Clone
        if os.path.isdir(github_url):
            # 로컬 경로인 경우
            print(f"📂 Local directory detected: {github_url}")
            print("ℹ️ Skipping git clone for local path.")
            repo_path = github_url
            should_cleanup = False  # 로컬 원본 폴더는 삭제하면 안 됨
        else:
            # 원격 URL인 경우
            print("📥 Step 1: Cloning repository...")
            repo_path = clone_repository(github_url)
            should_cleanup = True   # 임시로 Clone한 폴더는 삭제해야 함
            print(f"✅ Cloned to: {repo_path}\n")
        
        # 2. 언어 분석 및 분류
        print("📊 Step 2: Analyzing languages...")
        analyzer = RepositoryAnalyzer()
        analysis_result = analyzer.analyze(repo_path)
        print(f"✅ Language analysis completed\n")
        
        # 3. SAST 스캔
        print("🔍 Step 3: Running SAST Scanner...")
        sast_scanner = SASTScanner()
        sast_report = sast_scanner.scan_repository(
            analysis_result.scanner_targets.sast_targets
        )
        print(f"✅ SAST scan completed\n")
        
        # 4. SCA 스캔
        print("📦 Step 4: Running SCA Scanner...")
        sca_scanner = SCAScanner()
        sca_report = sca_scanner.scan_repository(
            analysis_result.scanner_targets.sca_targets
        )
        print(f"✅ SCA scan completed\n")
        
        # 5. Config 스캔
        print("⚙️  Step 5: Running Config Scanner...")
        config_scanner = ConfigScanner()
        config_report = config_scanner.scan_repository(
            analysis_result.scanner_targets.config_targets
        )
        print(f"✅ Config scan completed\n")
        
        # 6. 결과 통합
        total_issues = (
            sast_report.total_vulnerabilities +
            sca_report.total_vulnerable +
            config_report.total_findings
        )
        
        result = CompleteScanResult(
            repository_url=github_url,
            repository_path=repo_path,
            language_analysis={
                "total_files": analysis_result.total_files,
                "language_stats": [
                    {
                        "language": stat.language,
                        "file_count": stat.file_count,
                        "total_lines": stat.total_lines,
                        "percentage": stat.percentage
                    }
                    for stat in analysis_result.language_stats
                ]
            },
            sast_report={
                "total_files_scanned": sast_report.total_files_scanned,
                "total_vulnerabilities": sast_report.total_vulnerabilities,
                "severity_breakdown": sast_report.severity_breakdown,
                "algorithm_breakdown": sast_report.algorithm_breakdown,
                "details": [
                    {
                        "file_path": r.file_path,
                        "language": r.language,
                        "vulnerabilities": r.vulnerabilities,
                        "total_issues": r.total_issues
                    }
                    for r in sast_report.detailed_results
                    if not r.skipped and r.total_issues > 0
                ]
            },
            sca_report={
                "total_files_scanned": sca_report.total_files_scanned,
                "total_dependencies": sca_report.total_dependencies,
                "total_vulnerable": sca_report.total_vulnerable,
                "details": [
                    {
                        "file_path": r.file_path,
                        "vulnerable_dependencies": r.vulnerable_dependencies
                    }
                    for r in sca_report.detailed_results
                    if not r.skipped and r.total_vulnerabilities > 0
                ]
            },
            config_report={
                "total_files_scanned": config_report.total_files_scanned,
                "total_findings": config_report.total_findings,
                "details": [
                    {
                        "file_path": r.file_path,
                        "findings": r.findings
                    }
                    for r in config_report.detailed_results
                    if not r.skipped and r.total_findings > 0
                ]
            },
            total_issues=total_issues
        )
        
        print(f"\n{'='*60}")
        print(f"✅ Scan completed successfully!")
        print(f"📊 Total issues found: {total_issues}")
        print(f"{'='*60}\n")
        
        # 결과를 dict로 변환
        result_dict = {
            "repository_url": result.repository_url,
            "language_analysis": result.language_analysis,
            "sast_report": result.sast_report,
            "sca_report": result.sca_report,
            "config_report": result.config_report,
            "total_issues": result.total_issues,
            "scanned_at": result.scanned_at.isoformat()
        }
        
        return ScanResponse(
            status="success",
            message="Scan completed successfully",
            result=result_dict
        )
    
    except Exception as e:
        print(f"\n❌ Error during scan: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 임시 디렉토리 정리 (should_cleanup이 True일 때만 삭제)
        if should_cleanup and repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
                print(f"🗑️  Cleaned up: {repo_path}")
            except:
                pass

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
