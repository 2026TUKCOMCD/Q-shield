import asyncio
import os
import sys
import uuid as uuid_lib
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai_module.orchestrator import analyze_findings
from app.ai_module.schemas import AiAnalysisResponse
from app.models import Finding, Scan
import app.routes.scans as scans
from app.scan_read_service import get_findings_response


class _FakeBinary:
    def __init__(self, expression):
        self.key = expression.left.key
        self.value = getattr(expression.right, "value", None)


class FakeQuery:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, *expressions):
        filtered = self._items
        for expression in expressions:
            binary = _FakeBinary(expression)
            filtered = [item for item in filtered if getattr(item, binary.key) == binary.value]
        return FakeQuery(filtered)

    def order_by(self, *_args, **_kwargs):
        return self

    def offset(self, value):
        return FakeQuery(self._items[value:])

    def limit(self, value):
        return FakeQuery(self._items[:value])

    def count(self):
        return len(self._items)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class FakeDB:
    def __init__(self, *, scans_data=None, findings_data=None):
        self._mapping = {
            Scan: list(scans_data or []),
            Finding: list(findings_data or []),
        }

    def query(self, model):
        return FakeQuery(self._mapping.get(model, []))


def _build_finding_record(scan_uuid, item_id, severity, context, file_path):
    return SimpleNamespace(
        id=item_id,
        scan_uuid=scan_uuid,
        type="rsa_generation",
        severity=severity,
        algorithm="RSA",
        context=context,
        file_path=file_path,
        line_start=10,
        line_end=10,
        evidence="RSA.generate(2048)",
        meta={"scanner_type": context, "rule_id": "rsa_generation"},
    )


def _sample_ai_payload():
    return AiAnalysisResponse.model_validate(
        {
            "risk_score": 55,
            "pqc_readiness_score": 60,
            "severity_weighted_index": 2.4,
            "refactor_cost_estimate": {
                "level": "MEDIUM",
                "explanation": "4 files affected, distributed usage.",
                "affected_files": 4,
            },
            "priority_rank": 3,
            "recommendations": [
                {
                    "title": "Replace RSA with ML-KEM",
                    "description": "Migrate quantum-vulnerable key exchange.",
                    "nist_standard_reference": "FIPS 203 (ML-KEM)",
                    "citations": [],
                    "confidence": 0.5,
                }
            ],
            "analysis_summary": "Sample snapshot",
            "confidence_score": 0.5,
            "citation_missing": True,
            "inputs_summary": {"counts_by_scanner_type": {"SAST": 1}},
        }
    )


def test_findings_api_schema_and_filters():
    scan_uuid = uuid_lib.uuid4()
    user_uuid = uuid_lib.uuid4()
    db = FakeDB(
        scans_data=[SimpleNamespace(uuid=scan_uuid, user_uuid=user_uuid)],
        findings_data=[
            _build_finding_record(scan_uuid, 1, "HIGH", "SAST", "src/auth.py"),
            _build_finding_record(scan_uuid, 2, "LOW", "CONFIG", "nginx.conf"),
        ],
    )

    response = get_findings_response(
        db,
        scan_uuid,
        scanner_type="sast",
        severity="high",
        limit=1,
        offset=0,
        user_uuid=user_uuid,
    )

    assert response.scan_id == str(scan_uuid)
    assert response.total == 1
    assert response.limit == 1
    assert len(response.items) == 1
    assert response.items[0].context == "SAST"
    assert response.items[0].severity == "HIGH"
    assert response.items[0].meta["rule_id"] == "rsa_generation"


def test_ai_analysis_post_enqueues_task_and_get_returns_saved_snapshot(monkeypatch):
    scan_uuid = uuid_lib.uuid4()
    user_uuid = uuid_lib.uuid4()
    fake_scan = SimpleNamespace(uuid=scan_uuid)
    delayed_calls = []
    payload = _sample_ai_payload()

    class FakeScopedQuery:
        def __init__(self, result):
            self._result = result

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self._result

    monkeypatch.setattr(scans, "_scoped_scan_query", lambda _db, _user_uuid: FakeScopedQuery(fake_scan))
    monkeypatch.setattr(scans, "get_ai_analysis_snapshot", lambda _db, _scan_uuid: None)
    monkeypatch.setattr(scans.run_ai_analysis, "delay", lambda value: delayed_calls.append(value))

    start_response = scans.create_ai_analysis(str(scan_uuid), db=object(), user_uuid=user_uuid)

    assert start_response.status == "QUEUED"
    assert start_response.scan_id == str(scan_uuid)
    assert delayed_calls == [str(scan_uuid)]

    snapshot = SimpleNamespace(scan_uuid=scan_uuid)
    monkeypatch.setattr(scans, "get_ai_analysis_snapshot", lambda _db, _scan_uuid: snapshot)
    monkeypatch.setattr(scans, "serialize_ai_analysis_snapshot", lambda _snapshot: payload)

    get_response = scans.get_ai_analysis(str(scan_uuid), db=object(), user_uuid=user_uuid)

    assert get_response.risk_score == 55
    assert get_response.recommendations[0].nist_standard_reference == "FIPS 203 (ML-KEM)"


def test_duplicate_noise_does_not_break_ai_analysis():
    finding = {
        "type": "rsa_generation",
        "severity": "HIGH",
        "algorithm": "RSA",
        "context": "SAST",
        "file_path": "src/auth.py",
        "line_start": 12,
        "line_end": 12,
        "evidence": "RSA.generate(2048)",
        "meta": {"scanner_type": "SAST", "rule_id": "rsa_generation"},
    }

    response, _citations, _references = asyncio.run(analyze_findings([finding, dict(finding)], corpus_path="Z:\\missing"))

    assert response.inputs_summary["total_findings"] == 1
    assert response.inputs_summary["source_findings"] == 2
    assert response.priority_rank >= 1
    assert response.recommendations


def test_rag_fallback_marks_citation_missing():
    finding = {
        "type": "node-rsa",
        "severity": "HIGH",
        "algorithm": None,
        "context": "SCA",
        "file_path": "requirements.txt",
        "line_start": None,
        "line_end": None,
        "evidence": "node-rsa@1.0.0",
        "meta": {
            "scanner_type": "SCA",
            "rule_id": "node-rsa",
            "library": "node-rsa",
            "usage_type": "dependency",
        },
    }

    response, citations, references = asyncio.run(analyze_findings([finding], corpus_path="Z:\\missing"))

    assert response.citation_missing is True
    assert response.confidence_score < 0.8
    assert citations == []
    assert references == ["N/A"]
