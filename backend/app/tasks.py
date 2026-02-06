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

# Add scanner module path so Celery worker can import it.
SCANNER_PATH = Path(__file__).parent.parent.parent / "3_scanner"
sys.path.insert(0, str(SCANNER_PATH))

# Scanner imports
from language_detector.repository_analyzer import RepositoryAnalyzer  # noqa: E402
from scanners.config.scanner import ConfigScanner  # noqa: E402
from scanners.sast.scanner import SASTScanner  # noqa: E402
from scanners.sca.scanner import SCAScanner  # noqa: E402
from utils.git_utils import clone_repository  # noqa: E402

# Celery runs outside FastAPI dependency scope, create a local session.
engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(name="run_scan_pipeline")
def run_scan_pipeline(scan_uuid: str):
    db = SessionLocal()
    scan_uuid_obj = None
    repo_path = None
    scan = None

    def _update(status=None, progress=None, message=None, error_log=None):
        """Update scan state and commit."""
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
        # String -> UUID (DB column is UUID)
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
        # config_report is not persisted yet.

        # 6) Process & Persist
        _update(progress=0.85, message="Processing results...")

        inv_data = {
            "pqc_readiness_score": _calculate_pqc_score(sast_report, sca_report),
            "algorithm_ratios": _extract_algorithm_ratios(sast_report),
            "inventory_table": _extract_inventory_table(sast_report, sca_report, repo_path),
        }
        heat_data = _build_heatmap_tree(repo_path, analysis_result, sast_report)
        recommendations = _extract_recommendations(sast_report, sca_report)

        # Persist results in a single transaction.
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

            # scan_uuid is PK/UNIQUE, use merge for upsert.
            db.merge(inv)
            db.merge(heat)

            # Replace recommendations for this scan_uuid.
            db.query(Recommendation).filter(Recommendation.scan_uuid == scan_uuid_obj).delete()
            for rec in recommendations:
                db.add(Recommendation(scan_uuid=scan_uuid_obj, **rec))

        _update(progress=0.95, message="Finalizing...")

        # 7) Done
        _update(status="COMPLETED", progress=1.0, message="Scan completed successfully")
        return

    except Exception as e:
        # Failure handling: update scan row if exists.
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
        # Clone repo cleanup
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception:
                pass
        db.close()


def _calculate_pqc_score(sast_report, sca_report) -> int:
    """Calculate a simple PQC readiness score (0-10)."""
    total_issues = 0

    # Safely check attributes
    if hasattr(sast_report, "total_vulnerabilities"):
        total_issues += int(sast_report.total_vulnerabilities or 0)
    if hasattr(sca_report, "total_vulnerable"):
        total_issues += int(sca_report.total_vulnerable or 0)

    if total_issues == 0:
        return 10
    return max(1, 10 - (total_issues // 5))


def _extract_algorithm_ratios(sast_report):
    """Extract algorithm ratios."""
    algo_count = getattr(sast_report, "algorithm_breakdown", {}) or {}
    total = sum(int(v or 0) for v in algo_count.values())
    if total <= 0:
        return []

    result = []
    for algo, count in algo_count.items():
        ratio = round((int(count or 0) / total), 2)
        result.append({"name": algo, "ratio": ratio})
    return result


def _normalize_repo_path(repo_root: Path, file_path: str) -> str:
    try:
        path = Path(file_path)
        if path.is_absolute():
            return path.relative_to(repo_root).as_posix()
        return path.as_posix()
    except Exception:
        return str(file_path)


def _read_code_snippet(repo_root: Path, file_path: str, line: int, context: int = 3):
    if not line or line < 1:
        return None, None

    path = Path(file_path)
    if not path.is_absolute():
        path = repo_root / path

    if not path.exists() or not path.is_file():
        return None, None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None, None

    if line > len(lines):
        return None, None

    start = max(1, line - context)
    end = min(len(lines), line + context)
    snippet = "".join(lines[start - 1 : end])
    return snippet, start


def _extract_inventory_table(sast_report, sca_report, repo_path: str):
    """Build inventory table from SAST results with code snippets."""
    inventory = []
    details = getattr(sast_report, "detailed_results", []) or []
    repo_root = Path(repo_path)

    for detail in details:
        vulns = getattr(detail, "vulnerabilities", None)
        file_path = getattr(detail, "file_path", None)

        if not vulns or not file_path:
            continue

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            algo = vuln.get("algorithm", "Unknown")
            line_raw = vuln.get("line", None)
            try:
                line = int(line_raw)
            except Exception:
                line = None

            normalized_path = _normalize_repo_path(repo_root, str(file_path))
            code_snippet, snippet_start = _read_code_snippet(repo_root, str(file_path), line or 0)
            detected_pattern = vuln.get("pattern") or vuln.get("detected_pattern")

            location = {
                "file_path": normalized_path,
                "line": line,
                "code_snippet": code_snippet,
                "code_snippet_start_line": snippet_start,
                "detected_pattern": detected_pattern,
            }

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
    """Build a full repository tree with aggregated risk scores."""
    file_risk_map = {}
    details = getattr(sast_report, "detailed_results", []) or []
    repo_root = Path(repo_path)
    skip_dirs = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}

    for detail in details:
        file_path = getattr(detail, "file_path", None)
        vulns = getattr(detail, "vulnerabilities", []) or []
        if not file_path:
            continue

        high = sum(1 for v in vulns if isinstance(v, dict) and v.get("severity") == "HIGH")
        med = sum(1 for v in vulns if isinstance(v, dict) and v.get("severity") == "MEDIUM")
        low = sum(1 for v in vulns if isinstance(v, dict) and v.get("severity") == "LOW")
        severity_score = min(10.0, (high * 3) + (med * 2) + (low * 1))

        normalized_path = _normalize_repo_path(repo_root, str(file_path))
        existing = float(file_risk_map.get(normalized_path, 0.0))
        file_risk_map[normalized_path] = max(existing, severity_score)

    root = {
        "name": repo_root.name,
        "path": "",
        "type": "dir",
        "risk_score": 0.0,
        "children": [],
    }

    dir_index = {"": root}

    def _get_or_create_dir(path_parts):
        current_path = ""
        for part in path_parts:
            next_path = f"{current_path}/{part}" if current_path else part
            if next_path not in dir_index:
                node = {"name": part, "path": next_path, "type": "dir", "risk_score": 0.0, "children": []}
                parent = dir_index[current_path]
                parent["children"].append(node)
                dir_index[next_path] = node
            current_path = next_path

    for file_path in repo_root.rglob("*"):
        if any(part in skip_dirs for part in file_path.parts):
            continue
        if file_path.is_dir():
            continue
        try:
            rel_path = file_path.relative_to(repo_root).as_posix()
        except Exception:
            rel_path = file_path.as_posix()

        parts = rel_path.split("/")
        dir_parts = parts[:-1]
        if dir_parts:
            _get_or_create_dir(dir_parts)

        parent_path = "/".join(dir_parts)
        parent = dir_index.get(parent_path, root)
        parent["children"].append(
            {
                "name": parts[-1],
                "path": rel_path,
                "type": "file",
                "risk_score": float(file_risk_map.get(rel_path, 0.0)),
                "children": [],
            }
        )

    def _aggregate(node):
        if node.get("type") == "file":
            return float(node.get("risk_score", 0.0))
        children = node.get("children") or []
        if not children:
            node["risk_score"] = 0.0
            return 0.0
        max_risk = 0.0
        for child in children:
            max_risk = max(max_risk, _aggregate(child))
        node["risk_score"] = max_risk
        return max_risk

    _aggregate(root)
    return root


def _extract_recommendations(sast_report, sca_report):
    """Extract basic recommendations from SAST results."""
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
