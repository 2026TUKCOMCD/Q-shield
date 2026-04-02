import asyncio
import os
import sys
import uuid as uuid_lib
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("AI_ALLOW_DETERMINISTIC_FALLBACK", "false")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai_module.orchestrator import analyze_findings
import app.ai_module.orchestrator as orchestrator
from app.ai_module.schemas import AffectedLocation, AiAnalysisResponse
from app.ai_module.validator import validate_ai_response
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


def test_ai_analysis_post_returns_ready_when_snapshot_exists(monkeypatch):
    scan_uuid = uuid_lib.uuid4()
    user_uuid = uuid_lib.uuid4()
    fake_scan = SimpleNamespace(uuid=scan_uuid)
    delayed_calls = []

    class FakeScopedQuery:
        def __init__(self, result):
            self._result = result

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self._result

    existing_snapshot = SimpleNamespace(scan_uuid=scan_uuid)
    monkeypatch.setattr(scans, "_scoped_scan_query", lambda _db, _user_uuid: FakeScopedQuery(fake_scan))
    monkeypatch.setattr(scans, "get_ai_analysis_snapshot", lambda _db, _scan_uuid: existing_snapshot)
    monkeypatch.setattr(scans.run_ai_analysis, "delay", lambda value: delayed_calls.append(value))

    response = scans.create_ai_analysis(str(scan_uuid), db=object(), user_uuid=user_uuid)

    assert response.status == "READY"
    assert response.scan_id == str(scan_uuid)
    assert response.ai_analysis_id == str(scan_uuid)
    assert delayed_calls == []


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
    assert response.analysis_mode in {"error", "fallback", "real"}


def test_rag_llm_payload_path_uses_mocked_generation(monkeypatch):
    finding = {
        "type": "rsa_generation",
        "severity": "CRITICAL",
        "algorithm": "RSA-2048",
        "context": "SAST",
        "file_path": "src/auth.py",
        "line_start": 33,
        "line_end": 33,
        "evidence": "RSA.generate(2048)",
        "meta": {"scanner_type": "SAST", "rule_id": "rsa_generation"},
    }

    monkeypatch.setattr(
        orchestrator,
        "inspect_rag_corpus",
        lambda _corpus_path=None: SimpleNamespace(
            to_dict=lambda: {
                "rag_corpus_loaded": True,
                "vector_store_ready": True,
                "vector_count": 10,
                "vector_store_collection": "qshield_nist_rag",
            }
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "retrieve_relevant_chunks_with_debug",
        lambda _query, top_k=8: SimpleNamespace(
            chunks=[
                {
                    "doc_id": "fips203.pdf",
                    "title": "FIPS 203",
                    "section": "page 12",
                    "page": 12,
                    "url": None,
                    "text": "ML-KEM replaces classical key establishment.",
                }
            ],
            failure_reason=None,
            vector_store_collection="qshield_nist_rag",
        ),
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_grounded_ai_analysis",
        lambda **_kwargs: {
            "risk_score": 77,
            "pqc_readiness_score": 31,
            "severity_weighted_index": 4.2,
            "refactor_cost_estimate": {
                "level": "MEDIUM",
                "explanation": "1 files affected, centralized usage.",
                "affected_files": 1,
            },
            "priority_rank": 1,
            "recommendations": [
                {
                    "title": "Adopt ML-KEM for key establishment",
                    "description": "Replace RSA key establishment code paths.",
                    "nist_standard_reference": "FIPS 203 (ML-KEM)",
                    "citations": [
                        {
                            "doc_id": "fips203.pdf",
                            "title": "FIPS 203",
                            "section": "page 12",
                            "page": 12,
                            "url": None,
                            "snippet": "ML-KEM replaces classical key establishment.",
                        }
                    ],
                    "confidence": 0.84,
                }
            ],
            "analysis_summary": "Critical RSA usage should migrate to ML-KEM.",
            "confidence_score": 0.84,
            "citation_missing": False,
            "inputs_summary": {"total_findings": 1},
        },
    )

    response, citations, references = asyncio.run(analyze_findings([finding], corpus_path="Z:\\missing"))

    assert response.risk_score == 77
    assert response.citation_missing is False
    assert citations[0]["doc_id"] == "fips203.pdf"
    assert references == ["FIPS 203 (ML-KEM)"]
    assert response.recommendations[0].priority_reason


def test_benchmark_support_links_notes_to_benchmark_citations():
    support = orchestrator._build_benchmark_support(
        [
            "Use NIST SP 1800-38C style measurements for handshake latency and certificate size.",
        ],
        [
            SimpleNamespace(
                doc_id="38c.pdf",
                page=14,
                title="NIST SP 1800-38C",
                topic="certificate_size",
                snippet="Certificate chain size and handshake latency should be measured.",
                source_type="BENCHMARK",
            )
        ],
    )

    assert len(support) == 1
    assert support[0]["note"].startswith("Use NIST SP 1800-38C")
    assert support[0]["citation_keys"] == ["38c.pdf:14"]
    assert support[0]["citation_titles"] == ["NIST SP 1800-38C"]
    assert response.recommendations[0].validation_checklist
    assert response.recommendations[0].benchmark_notes
    assert response.recommendations[0].assumptions
    assert response.recommendations[0].confidence_reason


def test_rag_failure_returns_fallback_mode_when_enabled(monkeypatch):
    monkeypatch.setattr(orchestrator, "AI_ALLOW_DETERMINISTIC_FALLBACK", True)
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

    assert response.analysis_mode == "fallback"
    assert response.citation_missing is True
    assert response.confidence_score > 0.0
    assert response.recommendations
    assert citations == []
    assert references == ["N/A"]
    assert response.recommendations[0].validation_checklist
    assert response.recommendations[0].assumptions
    assert response.recommendations[0].confidence_reason


def test_validator_removes_quantified_security_claims():
    payload = AiAnalysisResponse.model_validate(
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
                    "description": "This migration improves security by 73%. Use ML-KEM instead.",
                    "nist_standard_reference": "FIPS 203 (ML-KEM)",
                    "citations": [],
                    "confidence": 0.7,
                    "benchmark_notes": ["Handshake performance improved by 45% in one setup."],
                }
            ],
            "analysis_summary": "Security improved by 80% after migration.",
            "confidence_score": 0.7,
            "citation_missing": True,
            "inputs_summary": {},
        }
    )

    validated = validate_ai_response(payload)

    assert "%" not in validated.analysis_summary
    assert "%" not in validated.recommendations[0].description
    assert all("%" not in note for note in validated.recommendations[0].benchmark_notes)
    assert validated.inputs_summary["validation"]["percentage_claims_removed"] >= 2
    assert validated.recommendations[0].confidence < payload.recommendations[0].confidence


def test_validator_downgrades_benchmark_only_normative_reference():
    payload = AiAnalysisResponse.model_validate(
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
                    "description": "Replace RSA key establishment.",
                    "nist_standard_reference": "FIPS 203 (ML-KEM)",
                    "citations": [
                        {
                            "doc_id": "38c.pdf",
                            "title": "SP 1800-38C",
                            "section": "page 12",
                            "page": 12,
                            "url": None,
                            "snippet": "Benchmark handshake latency in PQC migration.",
                            "source_type": "NIST_GUIDE",
                            "claim_type": "benchmark_guidance",
                            "topic": "tls,interop,performance",
                            "authority_weight": 95,
                        }
                    ],
                    "confidence": 0.8,
                    "confidence_reason": "1 supporting citations attached",
                }
            ],
            "analysis_summary": "Sample summary",
            "confidence_score": 0.8,
            "citation_missing": False,
            "inputs_summary": {},
        }
    )

    validated = validate_ai_response(payload)

    assert validated.recommendations[0].nist_standard_reference == "N/A"
    assert validated.recommendations[0].confidence < payload.recommendations[0].confidence
    assert "normative reference removed" in (validated.recommendations[0].confidence_reason or "")
    assert validated.inputs_summary["validation"]["benchmark_only_reference_downgrades"] == 1


def test_related_finding_selection_accepts_pydantic_affected_locations():
    findings = [
        {
            "type": "jwt_rsa_algorithm",
            "severity": "HIGH",
            "algorithm": "RSA",
            "context": "SAST",
            "file_path": "src/auth/token_service.py",
            "line_start": 12,
            "line_end": 12,
            "evidence": 'jwt.encode(payload, key, algorithm="RS256")',
            "meta": {"scanner_type": "SAST", "rule_id": "jwt_rsa_algorithm"},
        }
    ]
    affected_locations = [
        AffectedLocation(
            file_path="src/auth/token_service.py",
            line_start=12,
            line_end=12,
            rule_id="jwt_rsa_algorithm",
            scanner_type="SAST",
            evidence_excerpt='jwt.encode(payload, key, algorithm="RS256")',
        )
    ]

    related = orchestrator._select_related_findings(
        findings,
        affected_locations,
        "Migrate RSA-based JWT signing to a PQC-ready path.",
    )
    checklist = orchestrator._build_validation_checklist(
        "Migrate RSA-based JWT signing to a PQC-ready path.",
        affected_locations,
        ["SAST"],
    )
    benchmark_notes = orchestrator._build_benchmark_notes(
        "Migrate RSA-based JWT signing to a PQC-ready path.",
        ["SAST"],
        affected_locations,
    )
    fix_example = orchestrator._fallback_fix_example(
        "Migrate RSA-based JWT signing to a PQC-ready path.",
        affected_locations[0],
    )

    assert len(related) == 1
    assert related[0]["file_path"] == "src/auth/token_service.py"
    assert any("downstream consumers" in item for item in checklist)
    assert any("sign and verify latency" in item for item in benchmark_notes)
    assert fix_example is not None
    assert fix_example["file_path"] == "src/auth/token_service.py"


def test_fallback_fix_example_skips_certificate_and_config_assets():
    config_location = AffectedLocation(
        file_path="tests/certs/expired/ca/ca.crt",
        line_start=2,
        line_end=2,
        rule_id="rsa_certificate",
        scanner_type="CONFIG",
        evidence_excerpt="X.509 with RSA public key",
    )

    fix_example = orchestrator._fallback_fix_example(
        "Replace RSA certificate and signature paths with PQC-safe signature algorithms.",
        config_location,
    )

    assert fix_example is None
