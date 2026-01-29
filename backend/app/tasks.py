# backend/app/tasks.py
import os
import shutil
import sys
import time
import uuid as uuid_lib
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.config import DATABASE_URL_SYNC
from app.models import HeatmapSnapshot, InventorySnapshot, Recommendation, Scan

# 3_scanner 모듈 경로 추가 (Celery 워커 프로세스에서도 import 가능하도록)
SCANNER_PATH = Path(__file__).parent.parent.parent / "3_scanner"
sys.path.insert(0, str(SCANNER_PATH))

# 3_scanner 모듈 import
from language_detector.repository_analyzer import RepositoryAnalyzer  # noqa: E402
from scanners.config.scanner import ConfigScanner  # noqa: E402
from scanners.sast.scanner import SASTScanner  # noqa: E402
from scanners.sca.scanner import SCAScanner  # noqa: E402
from utils.git_utils import clone_repository  # noqa: E402

# Celery는 별도 프로세스라 FastAPI Dependency(get_db)를 못 씀 -> 엔진/세션을 별도 생성
engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(name="run_scan_pipeline")
def run_scan_pipeline(scan_uuid: str):
    db = SessionLocal()
    scan_uuid_obj = None
    repo_path = None
    scan = None

    def _update(status=None, progress=None, message=None, error_log=None):
        """Scan 상태 업데이트 헬퍼 (프론트 폴링용)."""
        nonlocal scan
        if scan is None:
            return
        if status is not None:
            scan.status = status
        if progress is not None:
            scan.progress = float(progress)
        if message is not None:
            scan.message = message
        if error_log is not None and hasattr(scan, "error_log"):
            scan.error_log = error_log
        db.commit()

    try:
        # 문자열 -> UUID (DB 컬럼 타입이 UUID)
        scan_uuid_obj = uuid_lib.UUID(scan_uuid)

        scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
        if not scan:
            return

        # 1) Clone
        _update(status="IN_PROGRESS", progress=0.10, message="Cloning repository...")
        repo_path = clone_repository(scan.github_url)

        # 2) Language analysis
        _update(progress=0.25, message="Analyzing languages...")
        analyzer = RepositoryAnalyzer()
        analysis_result = analyzer.analyze(repo_path)

        # 3) SAST
        _update(progress=0.40, message="Running SAST Scanner...")
        sast_scanner = SASTScanner()
        sast_report = sast_scanner.scan_repository(analysis_result.scanner_targets.sast_targets)

        # 4) SCA
        _update(progress=0.55, message="Running SCA Scanner...")
        sca_scanner = SCAScanner()
        sca_report = sca_scanner.scan_repository(analysis_result.scanner_targets.sca_targets)

        # 5) Config
        _update(progress=0.70, message="Running Config Scanner...")
        config_scanner = ConfigScanner()
        _ = config_scanner.scan_repository(analysis_result.scanner_targets.config_targets)
        # config_report는 현재 DB에 저장하지 않는 구조라면 변수 미사용 OK

        # 6) Process & Persist
        _update(progress=0.85, message="Processing results...")

        inv_data = {
            "pqc_readiness_score": _calculate_pqc_score(sast_report, sca_report),
            "algorithm_ratios": _extract_algorithm_ratios(sast_report),
            "inventory_table": _extract_inventory_table(sast_report, sca_report),
        }
        heat_data = _build_heatmap_tree(repo_path, analysis_result, sast_report)
        recommendations = _extract_recommendations(sast_report, sca_report)

        # 결과 저장은 한 트랜잭션으로 묶기
        with db.begin():
            inv = InventorySnapshot(
                scan_uuid=scan_uuid_obj,
                pqc_readiness_score=int(inv_data["pqc_readiness_score"] or 0),
                algorithm_ratios=inv_data["algorithm_ratios"] or [],
                inventory_table=inv_data["inventory_table"] or [],
            )

            heat = HeatmapSnapshot(
                scan_uuid=scan_uuid_obj,
                tree=heat_data or {},
            )

            # 같은 scan_uuid가 PK/UNIQUE면 merge로 교체
            db.merge(inv)
            db.merge(heat)

            # Recommendation은 여러 행: 기존 삭제 후 재삽입
            db.query(Recommendation).filter(Recommendation.scan_uuid == scan_uuid_obj).delete()
            for rec in recommendations:
                db.add(Recommendation(scan_uuid=scan_uuid_obj, **rec))

        _update(progress=0.95, message="Finalizing...")

        # 7) Done
        _update(status="COMPLETED", progress=1.0, message="Scan completed successfully")
        return

    except Exception as e:
        # 실패 처리: scan row가 남아있도록 업데이트
        try:
            if scan_uuid_obj is not None:
                scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
                if scan:
                    scan.status = "FAILED"
                    scan.progress = float(scan.progress or 0.0)
                    scan.message = f"Error: {str(e)}"
                    if hasattr(scan, "error_log"):
                        scan.error_log = str(e)
                    db.commit()
        except Exception:
            pass
        raise

    finally:
        # clone repo cleanup
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception:
                pass
        db.close()


def _calculate_pqc_score(sast_report, sca_report) -> int:
    """PQC 준비도 점수 계산 (0-10). 단순 휴리스틱."""
    total_issues = 0

    # 안전하게 attribute 존재 여부 확인
    if hasattr(sast_report, "total_vulnerabilities"):
        total_issues += int(sast_report.total_vulnerabilities or 0)
    if hasattr(sca_report, "total_vulnerable"):
        total_issues += int(sca_report.total_vulnerable or 0)

    if total_issues == 0:
        return 10
    return max(1, 10 - (total_issues // 5))


def _extract_algorithm_ratios(sast_report):
    """알고리즘별 비율 추출."""
    algo_count = getattr(sast_report, "algorithm_breakdown", {}) or {}
    total = sum(int(v or 0) for v in algo_count.values())
    if total <= 0:
        return []

    result = []
    for algo, count in algo_count.items():
        ratio = round((int(count or 0) / total), 2)
        result.append({"name": algo, "ratio": ratio})
    return result


def _extract_inventory_table(sast_report, sca_report):
    """인벤토리 테이블 생성 (SAST 기반)."""
    inventory = []
    details = getattr(sast_report, "detailed_results", []) or []

    for detail in details:
        vulns = getattr(detail, "vulnerabilities", None)
        file_path = getattr(detail, "file_path", None)

        if not vulns or not file_path:
            continue

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            algo = vuln.get("algorithm", "Unknown")
            line = vuln.get("line", "?")
            location = f"{file_path}:{line}"

            existing = next((i for i in inventory if i["algorithm"] == algo), None)
            if existing:
                existing["count"] += 1
                existing["locations"].append(location)
            else:
                inventory.append(
                    {
                        "algorithm": algo,
                        "count": 1,
                        "locations": [location],
                    }
                )

    return inventory


def _build_heatmap_tree(repo_path, analysis_result, sast_report):
    """히트맵 트리 구조 생성 (간단 버전: repo root만 반환)."""
    file_risk_map = {}
    details = getattr(sast_report, "detailed_results", []) or []

    for detail in details:
        file_path = getattr(detail, "file_path", None)
        vulns = getattr(detail, "vulnerabilities", []) or []
        if not file_path:
            continue

        high = sum(1 for v in vulns if isinstance(v, dict) and v.get("severity") == "HIGH")
        med = sum(1 for v in vulns if isinstance(v, dict) and v.get("severity") == "MEDIUM")
        severity_score = (high * 0.3) + (med * 0.2)
        file_risk_map[file_path] = min(1.0, float(severity_score) / 10.0)

    avg_risk = (sum(file_risk_map.values()) / max(len(file_risk_map), 1)) if file_risk_map else 0.0

    return {
        "name": Path(repo_path).name,
        "path": "",
        "type": "dir",
        "risk_score": avg_risk,
        "children": [],
    }


def _extract_recommendations(sast_report, sca_report):
    """권장사항 추출 (SAST 상세 취약점 기반, 상위 5개)."""
    recommendations = []
    details = getattr(sast_report, "detailed_results", []) or []

    rank = 1
    for detail in details:
        file_path = getattr(detail, "file_path", None) or ""
        vulns = getattr(detail, "vulnerabilities", []) or []

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            desc = vuln.get("description", "Issue detected")
            rec_txt = vuln.get("recommendation", "")
            algo = vuln.get("algorithm", "Unknown")

            recommendations.append(
                {
                    "priority_rank": rank,
                    "estimated_effort": "1-2 M/D",
                    "ai_recommendation": f"## {desc}\n{rec_txt}",
                    "algorithm": algo,
                    "context": file_path,
                }
            )
            rank += 1
            if len(recommendations) >= 5:
                return recommendations

    return recommendations
