import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai_module.llm.prompts import build_user_prompt
from app.ai_module.rag.loader import infer_document_metadata
from app.ai_module.rag.retriever import _sort_chunks_for_query


def test_infer_document_metadata_for_nist_and_benchmark_sources():
    metadata_8547 = infer_document_metadata(Path("NIST.IR.8547.ipd.pdf"))
    metadata_38b = infer_document_metadata(Path("pqc-migration-nist-sp-1800-38b-preliminary-draft.pdf"))
    metadata_38c = infer_document_metadata(Path("pqc-migration-nist-sp-1800-38c-preliminary-draft.pdf"))
    metadata_benchmark = infer_document_metadata(Path("oqs-tls-performance-benchmark.pdf"))

    assert metadata_8547["source_type"] == "NIST_GUIDE"
    assert metadata_8547["claim_type"] == "risk_guidance"
    assert "security-category" in metadata_8547["topic"]

    assert metadata_38b["source_type"] == "NIST_GUIDE"
    assert metadata_38b["claim_type"] == "migration_guidance"
    assert "inventory" in metadata_38b["topic"]

    assert metadata_38c["source_type"] == "NIST_GUIDE"
    assert metadata_38c["claim_type"] == "benchmark_guidance"
    assert "performance" in metadata_38c["topic"]

    assert metadata_benchmark["source_type"] == "BENCHMARK"
    assert metadata_benchmark["claim_type"] == "benchmark"


def test_build_user_prompt_includes_chunk_metadata_labels():
    prompt = build_user_prompt(
        findings=[
            {
                "type": "rsa_generation",
                "severity": "HIGH",
                "algorithm": "RSA",
                "context": "SAST",
                "file_path": "src/auth.py",
                "line_start": 10,
                "line_end": 10,
                "evidence": "RSA.generate(2048)",
                "meta": {"scanner_type": "SAST", "rule_id": "rsa_generation"},
            }
        ],
        retrieved_chunks=[
            {
                "doc_id": "NIST.IR.8547.ipd.pdf",
                "title": "NIST IR 8547",
                "section": "page 3",
                "page": 3,
                "text": "Transition planning should account for HNDL and migration timelines.",
                "source_type": "NIST_GUIDE",
                "claim_type": "risk_guidance",
                "topic": "migration-timeline,security-category,hndl",
            },
            {
                "doc_id": "pqc-migration-nist-sp-1800-38c-preliminary-draft.pdf",
                "title": "SP 1800-38C",
                "section": "page 18",
                "page": 18,
                "text": "Benchmark handshake latency and interoperability during PQC transition.",
                "source_type": "NIST_GUIDE",
                "claim_type": "benchmark_guidance",
                "topic": "tls,interop,performance",
            },
        ],
        risk_metrics={"risk_score": 80},
        refactor_cost_estimate={"level": "MEDIUM", "explanation": "test", "affected_files": 1},
        priority_rank=1,
        inputs_summary={"total_findings": 1},
    )

    assert "source_type=NIST_GUIDE" in prompt
    assert "claim_type=risk_guidance" in prompt
    assert "topic=tls,interop,performance" in prompt
    assert "RETRIEVED_NORMATIVE_CONTEXT" in prompt
    assert "RETRIEVED_BENCHMARK_CONTEXT" in prompt


def test_retriever_prefers_normative_chunks_for_migration_queries():
    chunks = [
        {
            "doc_id": "benchmark.pdf",
            "claim_type": "benchmark",
            "source_type": "BENCHMARK",
            "authority_weight": 70,
            "distance": 0.01,
        },
        {
            "doc_id": "8547.pdf",
            "claim_type": "risk_guidance",
            "source_type": "NIST_GUIDE",
            "authority_weight": 95,
            "distance": 0.2,
        },
    ]

    ranked = _sort_chunks_for_query(chunks, "pqc migration risk guidance for rsa transition", top_k=2)

    assert ranked[0]["doc_id"] == "8547.pdf"


def test_retriever_prefers_benchmark_chunks_for_performance_queries():
    chunks = [
        {
            "doc_id": "8547.pdf",
            "claim_type": "risk_guidance",
            "source_type": "NIST_GUIDE",
            "authority_weight": 95,
            "distance": 0.01,
        },
        {
            "doc_id": "38c.pdf",
            "claim_type": "benchmark_guidance",
            "source_type": "NIST_GUIDE",
            "authority_weight": 95,
            "distance": 0.2,
        },
    ]

    ranked = _sort_chunks_for_query(chunks, "benchmark handshake latency and interoperability for pqc tls", top_k=2)

    assert ranked[0]["doc_id"] == "38c.pdf"
