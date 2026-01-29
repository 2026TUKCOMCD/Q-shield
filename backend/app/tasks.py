import sys
import os
import shutil
import time
import uuid as uuid_lib
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL_SYNC
from app.models import Scan, InventorySnapshot, HeatmapSnapshot, Recommendation
from app.celery_app import celery_app

# 3_scanner 모듈 경로 추가
SCANNER_PATH = Path(__file__).parent.parent.parent / "3_scanner"
sys.path.insert(0, str(SCANNER_PATH))

# 3_scanner 모듈 import
from language_detector.repository_analyzer import RepositoryAnalyzer
from scanners.sast.scanner import SASTScanner
from scanners.sca.scanner import SCAScanner
from scanners.config.scanner import ConfigScanner
from utils.git_utils import clone_repository

# Celery는 별도 프로세스라 get_db(Dependency) 못 씀 -> 엔진을 따로 만든다
engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(name="run_scan_pipeline")
def run_scan_pipeline(scan_uuid: str):
    db = SessionLocal()
    scan_uuid_obj = None
    repo_path = None

    try:
        # 문자열 -> UUID로 변환 (DB 컬럼 타입이 UUID)
        scan_uuid_obj = uuid_lib.UUID(scan_uuid)

        scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
        if not scan:
            return

        # 1️⃣ Repository Clone
        scan.status = "IN_PROGRESS"
        scan.progress = 0.10
        scan.message = "Cloning repository..."
        db.commit()

        repo_path = clone_repository(scan.github_url)
        
        # 2️⃣ 언어 분석
        scan.progress = 0.25
        scan.message = "Analyzing languages..."
        db.commit()

        analyzer = RepositoryAnalyzer()
        analysis_result = analyzer.analyze(repo_path)

        # 3️⃣ SAST 스캔
        scan.progress = 0.40
        scan.message = "Running SAST Scanner..."
        db.commit()

        sast_scanner = SASTScanner()
        sast_report = sast_scanner.scan_repository(
            analysis_result.scanner_targets.sast_targets
        )

        # 4️⃣ SCA 스캔
        scan.progress = 0.55
        scan.message = "Running SCA Scanner..."
        db.commit()

        sca_scanner = SCAScanner()
        sca_report = sca_scanner.scan_repository(
            analysis_result.scanner_targets.sca_targets
        )

        # 5️⃣ Config 스캔
        scan.progress = 0.70
        scan.message = "Running Config Scanner..."
        db.commit()

        config_scanner = ConfigScanner()
        config_report = config_scanner.scan_repository(
            analysis_result.scanner_targets.config_targets
        )

        # 6️⃣ 결과 변환 및 저장
        scan.progress = 0.85
        scan.message = "Processing results..."
        db.commit()

        # InventorySnapshot 생성
        inv_data = {
            "pqc_readiness_score": _calculate_pqc_score(sast_report, sca_report),
            "algorithm_ratios": _extract_algorithm_ratios(sast_report),
            "inventory_table": _extract_inventory_table(sast_report, sca_report),
        }

        inv = InventorySnapshot(
            scan_uuid=scan_uuid_obj,
            pqc_readiness_score=inv_data["pqc_readiness_score"],
            algorithm_ratios=inv_data["algorithm_ratios"],
            inventory_table=inv_data["inventory_table"],
        )

        # HeatmapSnapshot 생성
        heat_data = _build_heatmap_tree(repo_path, analysis_result, sast_report)
        heat = HeatmapSnapshot(
            scan_uuid=scan_uuid_obj,
            tree=heat_data,
        )

        db.merge(inv)
        db.merge(heat)

        # Recommendation 생성
        db.query(Recommendation).filter(Recommendation.scan_uuid == scan_uuid_obj).delete()
        recommendations = _extract_recommendations(sast_report, sca_report)
        for rec in recommendations:
            db.add(Recommendation(scan_uuid=scan_uuid_obj, **rec))

        scan.progress = 0.95
        scan.message = "Finalizing..."
        db.commit()

        # 7️⃣ 완료
        scan.status = "COMPLETED"
        scan.progress = 1.0
        scan.message = "Scan completed successfully"
        db.commit()

    except Exception as e:
        # 실패 처리
        try:
            if scan_uuid_obj is not None:
                scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
                if scan:
                    scan.status = "FAILED"
                    scan.progress = scan.progress or 0.0
                    scan.message = f"Error: {str(e)}"
                    scan.error_log = str(e)
                    db.commit()
        except Exception:
            pass
        raise

    finally:
        # Repository 정리
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except:
                pass
        db.close()


def _calculate_pqc_score(sast_report, sca_report) -> int:
    """PQC 준비도 점수 계산 (0-10)"""
    total_issues = sast_report.total_vulnerabilities + sca_report.total_vulnerable
    if total_issues == 0:
        return 10
    return max(1, 10 - (total_issues // 5))


def _extract_algorithm_ratios(sast_report):
    """알고리즘별 비율 추출"""
    algo_count = sast_report.algorithm_breakdown
    total = sum(algo_count.values())
    if total == 0:
        return []
    
    return [
        {"name": algo, "ratio": round(count / total, 2)}
        for algo, count in algo_count.items()
    ]


def _extract_inventory_table(sast_report, sca_report):
    """인벤토리 테이블 생성"""
    inventory = []
    
    # SAST 결과에서 추출
    for detail in sast_report.detailed_results:
        if detail.vulnerabilities:
            for vuln in detail.vulnerabilities:
                algo = vuln.get("algorithm", "Unknown")
                location = f"{detail.file_path}:{vuln.get('line', '?')}"
                
                existing = next((i for i in inventory if i["algorithm"] == algo), None)
                if existing:
                    existing["count"] += 1
                    existing["locations"].append(location)
                else:
                    inventory.append({
                        "algorithm": algo,
                        "count": 1,
                        "locations": [location]
                    })
    
    return inventory


def _build_heatmap_tree(repo_path, analysis_result, sast_report):
    """히트맵 트리 구조 생성"""
    # 파일별 위험도 계산
    file_risk_map = {}
    for detail in sast_report.detailed_results:
        severity_score = sum(1 for v in detail.vulnerabilities if v.get("severity") == "HIGH") * 0.3 + \
                        sum(1 for v in detail.vulnerabilities if v.get("severity") == "MEDIUM") * 0.2
        file_risk_map[detail.file_path] = min(1.0, severity_score / 10)

    return {
        "name": Path(repo_path).name,
        "path": "",
        "type": "dir",
        "risk_score": sum(file_risk_map.values()) / max(len(file_risk_map), 1),
        "children": []
    }


def _extract_recommendations(sast_report, sca_report):
    """권장사항 추출"""
    recommendations = []
    
    for detail in sast_report.detailed_results:
        for i, vuln in enumerate(detail.vulnerabilities, 1):
            recommendations.append({
                "priority_rank": i,
                "estimated_effort": "1-2 M/D",
                "ai_recommendation": f"## {vuln.get('description')}\n{vuln.get('recommendation')}",
                "algorithm": vuln.get("algorithm", "Unknown"),
                "context": detail.file_path,
            })
    
    return sorted(recommendations, key=lambda x: x["priority_rank"])[:5]  # 상위 5개만
