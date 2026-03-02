from __future__ import annotations

from collections.abc import Iterable

from app.scoring.criteria import infer_algorithm_from_library, score_signal_points


def _build_signal(severity: str | None, algorithm: str | None) -> dict[str, str | None]:
    return {
        "severity": severity,
        "algorithm": algorithm,
    }


def build_score_signals_from_reports(sast_report, sca_report) -> list[dict[str, str | None]]:
    signals: list[dict[str, str | None]] = []

    for detail in getattr(sast_report, "detailed_results", []) or []:
        for vuln in getattr(detail, "vulnerabilities", []) or []:
            if not isinstance(vuln, dict):
                continue
            signals.append(_build_signal(vuln.get("severity"), vuln.get("algorithm")))

    for detail in getattr(sca_report, "detailed_results", []) or []:
        for dep in getattr(detail, "vulnerable_dependencies", []) or []:
            if not isinstance(dep, dict):
                continue
            library_name = dep.get("name") or dep.get("library_name")
            signals.append(_build_signal(dep.get("severity"), infer_algorithm_from_library(library_name)))

    return signals


def build_score_signals_from_findings(findings: Iterable[dict]) -> list[dict[str, str | None]]:
    signals: list[dict[str, str | None]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        meta = finding.get("meta") or {}
        algorithm = finding.get("algorithm")
        if not algorithm:
            algorithm = infer_algorithm_from_library(meta.get("library") or finding.get("type"))
        signals.append(_build_signal(finding.get("severity"), algorithm))
    return signals


def calculate_weighted_total(signals: Iterable[dict[str, str | None]]) -> float:
    total = 0.0
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        total += score_signal_points(signal.get("severity"), signal.get("algorithm"))
    return total


def compute_pqc_readiness_score(signals: Iterable[dict[str, str | None]], scale: int = 10) -> int:
    weighted_total = calculate_weighted_total(signals)
    if weighted_total <= 0:
        return 100 if scale == 100 else 10

    penalty = min(9.0, weighted_total / 3.0)
    legacy_score = int(max(1.0, 10.0 - penalty))
    if scale == 100:
        return legacy_score * 10
    return legacy_score


def compute_risk_score(signals: Iterable[dict[str, str | None]]) -> int:
    weighted_total = calculate_weighted_total(signals)
    if weighted_total <= 0:
        return 0
    normalized = min(1.0, weighted_total / 27.0)
    return int(round(normalized * 100))


def compute_severity_weighted_index(signals: Iterable[dict[str, str | None]]) -> float:
    signal_list = [signal for signal in signals if isinstance(signal, dict)]
    if not signal_list:
        return 0.0
    weighted_total = calculate_weighted_total(signal_list)
    return round(weighted_total / len(signal_list), 4)
