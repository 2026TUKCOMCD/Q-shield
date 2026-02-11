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
from app.models import Finding, HeatmapSnapshot, InventorySnapshot, Recommendation, Scan
from app.severity_map import CANONICAL_SEVERITIES, canonicalize_severity

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

        inv_data = {
            "pqc_readiness_score": _calculate_pqc_score(sast_report, sca_report),
            "algorithm_ratios": _extract_algorithm_ratios(sast_report),
            "inventory_table": _extract_inventory_table(sast_report, sca_report, repo_path),
        }
        heat_data = _build_heatmap_tree(repo_path, analysis_result, sast_report)
        recommendations = _extract_recommendations(sast_report, sca_report)
        findings = _normalize_findings(sast_report, sca_report, config_report, repo_path)

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
    """Calculate a PQC readiness score (0-10) using weighted risk signals."""
    severity_weight = {
        "CRITICAL": 4.0,
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0,
        "INFO": 0.5,
    }

    def _algo_weight(algo: str | None) -> float:
        if not algo:
            return 1.0
        text = str(algo).lower()
        if any(k in text for k in ("rsa", "ecc", "ecdsa", "dsa", "dh", "diffie")):
            return 1.6
        if any(k in text for k in ("md5", "sha1", "sha-1", "weak hash", "sha1")):
            return 1.3
        if any(k in text for k in ("aes", "chacha", "symmetric")):
            return 1.0
        return 1.0

    def _lib_to_algo(name: str | None) -> str:
        if not name:
            return "Unknown"
        text = str(name).lower()
        if any(k in text for k in ("rsa", "node-rsa", "python-rsa")):
            return "RSA"
        if any(k in text for k in ("ecdsa", "ecc", "elliptic")):
            return "ECC/ECDSA"
        if any(k in text for k in ("dsa", "dh", "diffie")):
            return "DSA/DH"
        if any(k in text for k in ("sha1", "sha-1", "md5")):
            return "Weak Hash"
        return "Unknown"

    weighted_total = 0.0

    # SAST
    for detail in getattr(sast_report, "detailed_results", []) or []:
        for vuln in getattr(detail, "vulnerabilities", []) or []:
            if not isinstance(vuln, dict):
                continue
            sev = str(vuln.get("severity", "MEDIUM")).upper()
            algo = vuln.get("algorithm")
            weighted_total += severity_weight.get(sev, 2.0) * _algo_weight(algo)

    # SCA
    for detail in getattr(sca_report, "detailed_results", []) or []:
        for dep in getattr(detail, "vulnerable_dependencies", []) or []:
            if not isinstance(dep, dict):
                continue
            sev = str(dep.get("severity", "MEDIUM")).upper()
            lib = dep.get("name") or dep.get("library_name")
            algo = _lib_to_algo(lib)
            weighted_total += severity_weight.get(sev, 2.0) * _algo_weight(algo)

    if weighted_total <= 0:
        return 10

    penalty = min(9.0, weighted_total / 3.0)
    score = int(max(1.0, 10.0 - penalty))
    return score


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

    severity_weight = {
        "CRITICAL": 4.0,
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0,
        "INFO": 0.5,
    }

    def _algo_weight(algo: str | None) -> float:
        if not algo:
            return 1.0
        text = str(algo).lower()
        if any(k in text for k in ("rsa", "ecc", "ecdsa", "dsa", "dh", "diffie")):
            return 1.6
        if any(k in text for k in ("md5", "sha1", "sha-1", "weak hash", "sha1")):
            return 1.3
        if any(k in text for k in ("aes", "chacha", "symmetric")):
            return 1.0
        return 1.0

    for detail in details:
        vulns = getattr(detail, "vulnerabilities", None)
        file_path = getattr(detail, "file_path", None)

        if not vulns or not file_path:
            continue

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            algo = vuln.get("algorithm", "Unknown")
            severity = str(vuln.get("severity", "MEDIUM")).upper()
            risk_points = severity_weight.get(severity, 2.0) * _algo_weight(algo)
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
                existing["risk_score"] = min(10.0, float(existing.get("risk_score", 0.0)) + risk_points)
            else:
                inventory.append(
                    {
                        "algorithm": algo,
                        "count": 1,
                        "locations": [location],
                        "risk_score": min(10.0, risk_points),
                    }
                )

    return inventory


def _build_heatmap_tree(repo_path, analysis_result, sast_report):
    """Build a full repository tree with aggregated risk scores."""
    file_risk_map = {}
    details = getattr(sast_report, "detailed_results", []) or []
    repo_root = Path(repo_path)
    skip_dirs = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}

    severity_weight = {
        "CRITICAL": 4.0,
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0,
        "INFO": 0.5,
    }

    def _algo_weight(algo: str | None) -> float:
        if not algo:
            return 1.0
        text = str(algo).lower()
        if any(k in text for k in ("rsa", "ecc", "ecdsa", "dsa", "dh", "diffie")):
            return 1.6
        if any(k in text for k in ("md5", "sha1", "sha-1", "weak hash", "sha1")):
            return 1.3
        if any(k in text for k in ("aes", "chacha", "symmetric")):
            return 1.0
        return 1.0

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
            severity_score += severity_weight.get(sev, 2.0) * _algo_weight(algo)
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


def _extract_recommendations(sast_report, sca_report):
    """Extract basic recommendations from SAST results."""
    def _to_text(value) -> str:
        if value is None:
            return ""
        return str(value)

    def _cap(value: str, limit: int) -> str:
        return value[:limit]

    recommendations = []
    details = getattr(sast_report, "detailed_results", []) or []

    rank = 1
    for detail in details:
        file_path = _to_text(getattr(detail, "file_path", None))
        vulns = getattr(detail, "vulnerabilities", []) or []

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            desc = _to_text(vuln.get("description", "Issue detected"))
            rec_txt = _to_text(vuln.get("recommendation", ""))
            algo = _cap(_to_text(vuln.get("algorithm", "Unknown")), 50)

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
