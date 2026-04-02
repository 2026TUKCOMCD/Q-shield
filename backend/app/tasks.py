import hashlib
import logging
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
from app.crypto_asset_ref import build_asset_ref, build_correlation_ref, canonical_algorithm_family
from app.models import Finding, HeatmapSnapshot, InventorySnapshot, Recommendation, Scan
from app.recommendation_planner import build_recommendation_plan
from app.scoring import build_score_signals_from_findings, compute_pqc_readiness_score, calculate_weighted_total
from app.scoring.criteria import score_signal_points
from app.severity_map import CANONICAL_SEVERITIES, canonicalize_severity
from app.tasks_ai import run_ai_analysis

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
logger = logging.getLogger(__name__)


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
        config_report = config_scanner.scan_repository(analysis_result.scanner_targets.config_targets)

        # 6) Process & Persist
        _update(progress=0.85, message="Processing results...")

        findings = _normalize_findings(sast_report, sca_report, config_report, repo_path)
        inv_data = {
            "pqc_readiness_score": _calculate_pqc_score_from_findings(findings),
            "algorithm_ratios": _extract_algorithm_ratios_from_findings(findings),
            "inventory_table": _extract_inventory_table_from_findings(findings, repo_path),
        }
        heat_data = _build_heatmap_tree(repo_path, analysis_result, sast_report)
        recommendations = _extract_recommendations_from_findings(findings)

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

            # Replace findings for this scan_uuid.
            db.query(Finding).filter(Finding.scan_uuid == scan_uuid_obj).delete()
            for finding in findings:
                db.add(Finding(scan_uuid=scan_uuid_obj, **finding))

        _update(progress=0.95, message="Finalizing...")

        # 7) Done
        _update(status="COMPLETED", progress=1.0, message="Scan completed successfully")
        try:
            run_ai_analysis.delay(str(scan_uuid_obj))
        except Exception as exc:
            logger.warning(
                "scan_pipeline stage=ai_analysis_enqueue_failed scan_uuid=%s reason=%s",
                str(scan_uuid_obj),
                str(exc),
            )
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


def _calculate_pqc_score_from_findings(findings: list[dict]) -> int:
    """Calculate a PQC readiness score (0-10) using normalized findings from all scanners."""
    signals = build_score_signals_from_findings(findings)
    return compute_pqc_readiness_score(signals, scale=10)


def _display_algorithm_label_from_finding(finding: dict) -> str:
    meta = finding.get("meta") or {}
    family = str(meta.get("algorithm_family") or "").lower()
    usage_type = str(meta.get("usage_type") or "").lower()
    algorithm = str(finding.get("algorithm") or "").strip()
    library = str(meta.get("library") or "").strip()

    if family == "rsa-public-key":
        return "RSA"
    if family == "dh-key-exchange":
        return "DH/ECDH"
    if family == "ecc-signature":
        return "ECC/ECDSA"
    if family == "dsa-signature":
        return "DSA"
    if family == "weak-hash":
        return "Weak Hash"
    if family == "private-key-material":
        return "Private Key Material"
    if usage_type == "dependency" and library:
        return "Legacy Crypto Dependency"
    if algorithm:
        return algorithm
    return "Legacy Crypto"


def _extract_algorithm_ratios_from_findings(findings: list[dict]):
    """Extract algorithm ratios from normalized findings across all scanners."""
    algo_count: dict[str, int] = {}
    total = 0
    for finding in findings or []:
        if not isinstance(finding, dict):
            continue
        meta = finding.get("meta") or {}
        count = int(meta.get("duplicate_count", 1) or 1)
        label = _display_algorithm_label_from_finding(finding)
        algo_count[label] = algo_count.get(label, 0) + count
        total += count

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


def _extract_inventory_table_from_findings(findings: list[dict], repo_path: str | None):
    """Build inventory table from normalized findings across SAST/SCA/CONFIG."""
    inventory: dict[str, dict] = {}
    repo_root = Path(repo_path) if repo_path else None

    for finding in findings or []:
        if not isinstance(finding, dict):
            continue

        meta = finding.get("meta") or {}
        algorithm_family = str(meta.get("algorithm_family") or canonical_algorithm_family(finding.get("algorithm")))
        usage_type = str(meta.get("usage_type") or "unknown")
        file_path = str(finding.get("file_path") or "unknown")
        asset_ref = str(
            meta.get("asset_ref")
            or build_asset_ref(
                usage_type=usage_type,
                algorithm_family=algorithm_family,
                file_path=file_path,
                library=meta.get("library"),
            )
        )
        correlation_ref = str(
            meta.get("correlation_ref")
            or build_correlation_ref(algorithm_family=algorithm_family, file_path=file_path)
        )
        inventory_id = asset_ref or f"{algorithm_family}:{file_path}"
        display_algorithm = _display_algorithm_label_from_finding(finding)

        line = finding.get("line_start")
        try:
            line = int(line) if line is not None else None
        except Exception:
            line = None

        normalized_path = _normalize_repo_path(repo_root, file_path) if repo_root else str(file_path)
        code_snippet = None
        snippet_start = None
        detected_pattern = meta.get("detected_pattern")
        if usage_type == "code" and repo_root and line:
            code_snippet, snippet_start = _read_code_snippet(repo_root, file_path, line)

        location = {
            "file_path": normalized_path,
            "line": line,
            "code_snippet": code_snippet,
            "code_snippet_start_line": snippet_start,
            "detected_pattern": detected_pattern,
            "scanner_type": meta.get("scanner_type"),
        }

        bucket = inventory.setdefault(
            inventory_id,
            {
                "algorithm": display_algorithm,
                "count": 0,
                "locations": [],
                "risk_score": 0.0,
                "asset_ref": asset_ref or None,
                "correlation_ref": correlation_ref or None,
                "algorithm_family": algorithm_family or None,
                "_findings": [],
                "_location_keys": set(),
            },
        )
        bucket["count"] += int(meta.get("duplicate_count", 1) or 1)
        bucket["_findings"].append(finding)

        location_key = (
            location.get("file_path"),
            location.get("line"),
            meta.get("rule_id"),
            meta.get("scanner_type"),
        )
        if location_key not in bucket["_location_keys"]:
            bucket["_location_keys"].add(location_key)
            bucket["locations"].append(location)

    normalized_inventory: list[dict] = []
    for bucket in inventory.values():
        signals = build_score_signals_from_findings(bucket["_findings"])
        bucket["risk_score"] = min(10.0, round(calculate_weighted_total(signals), 1))
        bucket.pop("_findings", None)
        bucket.pop("_location_keys", None)
        normalized_inventory.append(bucket)

    normalized_inventory.sort(
        key=lambda item: (
            -float(item.get("risk_score", 0.0) or 0.0),
            str(item.get("algorithm", "")),
            str(item.get("asset_ref", "")),
        )
    )
    return normalized_inventory


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

        severity_score = 0.0
        for v in vulns:
            if not isinstance(v, dict):
                continue
            sev = str(v.get("severity", "MEDIUM")).upper()
            algo = v.get("algorithm")
            severity_score += score_signal_points(sev, algo)
        severity_score = min(10.0, severity_score)

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


def _extract_recommendations(sast_report, sca_report, config_report):
    """Build deterministic recommendations from normalized scanner findings."""
    findings = _normalize_findings(sast_report, sca_report, config_report, None)
    return _extract_recommendations_from_findings(findings)


def _extract_recommendations_from_findings(findings: list[dict]):
    recommendations = []
    for item in build_recommendation_plan(findings):
        recommendations.append(
            {
                "priority_rank": int(item["priority_rank"]),
                "estimated_effort": str(item["estimated_effort"])[:20],
                "ai_recommendation": str(item["ai_recommendation"]),
                "algorithm": str(item["algorithm"])[:50],
                "context": str(item["context"])[:1000],
            }
        )
    return recommendations


def _normalize_findings(sast_report, sca_report, config_report, repo_path: str | None):
    """Normalize findings from all scanners into a unified schema."""
    findings: list[dict] = []
    repo_root = Path(repo_path) if repo_path else None

    def _cap(value: str | None, limit: int) -> str | None:
        if value is None:
            return None
        text = str(value)
        return text[:limit]

    def _normalize_path(file_path: str | None) -> str | None:
        if not file_path:
            return None
        if repo_root:
            return _normalize_repo_path(repo_root, file_path)
        return str(file_path)

    def _safe_int(value):
        try:
            return int(value)
        except Exception:
            return None

    def _hash_evidence(value: str | None) -> str:
        if not value:
            return ""
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()

    def _validate_finding(payload: dict) -> bool:
        required_keys = (
            "type",
            "severity",
            "file_path",
            "line_start",
            "line_end",
            "evidence",
            "meta",
        )
        for key in required_keys:
            if key not in payload:
                logger.warning("Skipping finding: missing key=%s payload=%s", key, payload)
                return False

        if payload["severity"] not in CANONICAL_SEVERITIES:
            logger.warning("Skipping finding: invalid severity=%s", payload["severity"])
            return False

        if payload["file_path"] is not None and not isinstance(payload["file_path"], str):
            logger.warning("Skipping finding: file_path not str/null payload=%s", payload)
            return False

        for line_key in ("line_start", "line_end"):
            line_val = payload.get(line_key)
            if line_val is not None and not isinstance(line_val, int):
                logger.warning("Skipping finding: %s not int/null payload=%s", line_key, payload)
                return False

        evidence = payload.get("evidence")
        if evidence is not None and not isinstance(evidence, str):
            logger.warning("Skipping finding: evidence not str/null payload=%s", payload)
            return False

        meta = payload.get("meta")
        if not isinstance(meta, dict):
            logger.warning("Skipping finding: meta not dict payload=%s", payload)
            return False

        if not meta.get("scanner_type") or not meta.get("rule_id") or "message" not in meta:
            logger.warning("Skipping finding: missing meta keys payload=%s", payload)
            return False

        return True

    def _dedup_findings(items: list[dict]) -> list[dict]:
        seen: dict[tuple, dict] = {}
        ordered: list[dict] = []
        for payload in items:
            meta = payload.get("meta") or {}
            key = (
                meta.get("scanner_type"),
                meta.get("rule_id"),
                payload.get("file_path"),
                payload.get("line_start"),
                payload.get("line_end"),
                _hash_evidence(payload.get("evidence")),
            )
            if key in seen:
                existing = seen[key]
                existing_meta = existing.get("meta") or {}
                existing_meta["duplicate_count"] = int(existing_meta.get("duplicate_count", 1)) + 1
                existing["meta"] = existing_meta
                continue
            seen[key] = payload
            ordered.append(payload)
        return ordered

    def _add_finding(
        *,
        scanner_type: str,
        rule_id: str,
        severity: str | None,
        file_path: str | None,
        line: int | None,
        message: str | None,
        evidence: str | None,
        algorithm: str | None = None,
        meta: dict | None = None,
    ):
        if severity is not None and not isinstance(severity, str):
            logger.warning("Skipping finding: invalid severity type=%s", type(severity).__name__)
            return
        canonical_severity, severity_score = canonicalize_severity(severity)
        payload = {
            "type": _cap(rule_id or scanner_type, 20) or scanner_type,
            "severity": canonical_severity,
            "algorithm": algorithm,
            "context": scanner_type,
            "file_path": _normalize_path(file_path),
            "line_start": line,
            "line_end": line,
            "evidence": evidence,
            "meta": meta or {},
        }
        payload["meta"].update(
            {
                "scanner_type": scanner_type,
                "rule_id": rule_id,
                "message": message or "",
                "severity_score": severity_score,
            }
        )
        usage_type = str(payload["meta"].get("usage_type") or "unknown")
        algorithm_family = canonical_algorithm_family(
            algorithm,
            rule_id=rule_id,
            library=payload["meta"].get("library"),
            message=message,
        )
        payload["meta"].update(
            {
                "algorithm_family": algorithm_family,
                "asset_ref": build_asset_ref(
                    usage_type=usage_type,
                    algorithm_family=algorithm_family,
                    file_path=payload["file_path"],
                    library=payload["meta"].get("library"),
                ),
                "correlation_ref": build_correlation_ref(
                    algorithm_family=algorithm_family,
                    file_path=payload["file_path"],
                ),
            }
        )
        if _validate_finding(payload):
            findings.append(payload)

    # SAST findings
    for detail in getattr(sast_report, "detailed_results", []) or []:
        file_path = getattr(detail, "file_path", None)
        for vuln in getattr(detail, "vulnerabilities", []) or []:
            if not isinstance(vuln, dict):
                continue
            rule_id = str(vuln.get("type") or "sast_issue")
            severity = vuln.get("severity", "MEDIUM")
            algorithm = vuln.get("algorithm")
            message = vuln.get("description") or "SAST issue detected"
            line = _safe_int(vuln.get("line"))
            evidence = vuln.get("code")
            if not evidence and repo_root and file_path and line:
                snippet, _ = _read_code_snippet(repo_root, file_path, line)
                evidence = snippet
            meta = {
                "usage_type": "code",
                "recommendation": vuln.get("recommendation"),
                "detected_pattern": vuln.get("pattern") or vuln.get("detected_pattern"),
            }
            _add_finding(
                scanner_type="SAST",
                rule_id=rule_id,
                severity=severity,
                file_path=file_path,
                line=line,
                message=message,
                evidence=evidence,
                algorithm=algorithm,
                meta=meta,
            )

    # SCA findings
    for detail in getattr(sca_report, "detailed_results", []) or []:
        file_path = getattr(detail, "file_path", None)
        for dep in getattr(detail, "vulnerable_dependencies", []) or []:
            if not isinstance(dep, dict):
                continue
            name = dep.get("name") or "dependency"
            rule_id = str(name)
            severity = dep.get("severity", "MEDIUM")
            message = dep.get("reason") or "Vulnerable dependency detected"
            current_version = dep.get("current_version")
            evidence = f"{name}@{current_version}" if current_version else str(name)
            meta = {
                "usage_type": "dependency",
                "library": name,
                "current_version": current_version,
                "dependency_type": dep.get("dependency_type"),
                "pqc_support": dep.get("pqc_support"),
                "pqc_version": dep.get("pqc_version"),
                "alternatives": dep.get("alternatives", []),
            }
            _add_finding(
                scanner_type="SCA",
                rule_id=rule_id,
                severity=severity,
                file_path=file_path,
                line=None,
                message=message,
                evidence=evidence,
                algorithm=None,
                meta=meta,
            )

    # Config findings
    algo_map = {
        "rsa_cipher": "RSA",
        "ecdsa_cipher": "ECC",
        "rsa_certificate": "RSA",
        "ecc_certificate": "ECC",
    }
    for detail in getattr(config_report, "detailed_results", []) or []:
        file_path = getattr(detail, "file_path", None)
        for finding in getattr(detail, "findings", []) or []:
            if not isinstance(finding, dict):
                continue
            rule_id = str(finding.get("type") or "config_issue")
            severity = finding.get("severity", "MEDIUM")
            message = finding.get("description") or "Config issue detected"
            line = _safe_int(finding.get("line"))
            evidence = finding.get("matched_text")
            if not evidence and repo_root and file_path and line:
                snippet, _ = _read_code_snippet(repo_root, file_path, line)
                evidence = snippet
            algorithm = algo_map.get(rule_id)
            meta = {
                "usage_type": "config",
                "recommendation": finding.get("recommendation"),
            }
            _add_finding(
                scanner_type="CONFIG",
                rule_id=rule_id,
                severity=severity,
                file_path=file_path,
                line=line,
                message=message,
                evidence=evidence,
                algorithm=algorithm,
                meta=meta,
            )

    return _dedup_findings(findings)
