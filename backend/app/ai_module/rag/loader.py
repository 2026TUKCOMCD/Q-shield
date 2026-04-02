from __future__ import annotations

from pathlib import Path
from typing import Iterator
import re

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency in tests
    PdfReader = None


def infer_document_metadata(file_path: Path) -> dict:
    normalized_name = file_path.stem.lower()
    normalized_name = normalized_name.replace("_", "-").replace(" ", "-")

    if re.search(r"fips[-\.]?20[345]", normalized_name):
        topics = {
            "203": "ml-kem,key-establishment,nist-standard",
            "204": "ml-dsa,signatures,nist-standard",
            "205": "slh-dsa,signatures,nist-standard",
        }
        matched = re.search(r"20([345])", normalized_name)
        suffix = f"20{matched.group(1)}" if matched else ""
        return {
            "source_type": "NIST_STANDARD",
            "claim_type": "normative",
            "topic": topics.get(suffix[-3:], "nist-standard"),
            "authority_weight": 100,
        }

    if "1800-38b" in normalized_name:
        return {
            "source_type": "NIST_GUIDE",
            "claim_type": "migration_guidance",
            "topic": "discovery,inventory,normalization,cbom",
            "authority_weight": 95,
        }

    if "1800-38c" in normalized_name:
        return {
            "source_type": "NIST_GUIDE",
            "claim_type": "benchmark_guidance",
            "topic": "tls,quic,interop,performance,certificates",
            "authority_weight": 95,
        }

    if "8547" in normalized_name:
        return {
            "source_type": "NIST_GUIDE",
            "claim_type": "risk_guidance",
            "topic": "migration-timeline,security-category,hndl,transition-planning",
            "authority_weight": 95,
        }

    if any(token in normalized_name for token in ("benchmark", "performance", "latency", "throughput")):
        return {
            "source_type": "BENCHMARK",
            "claim_type": "benchmark",
            "topic": "performance,interop",
            "authority_weight": 75,
        }

    if any(token in normalized_name for token in ("paper", "study", "analysis", "report")):
        return {
            "source_type": "ACADEMIC_PAPER",
            "claim_type": "research",
            "topic": "research",
            "authority_weight": 70,
        }

    return {
        "source_type": "UNKNOWN",
        "claim_type": "unknown",
        "topic": "general",
        "authority_weight": 50,
    }


def load_pdf_pages(pdf_path: Path) -> Iterator[dict]:
    if PdfReader is None:
        return
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return

    metadata = infer_document_metadata(pdf_path)

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if not text:
            continue
        yield {
            "doc_id": pdf_path.name,
            "title": pdf_path.stem,
            "page": page_number,
            "section": f"page {page_number}",
            "url": None,
            "text": text,
            "source_path": str(pdf_path),
            **metadata,
        }


def load_text_document(file_path: Path) -> Iterator[dict]:
    try:
        text = file_path.read_text(encoding="utf-8").strip()
    except Exception:
        return

    if not text:
        return

    metadata = infer_document_metadata(file_path)

    yield {
        "doc_id": file_path.name,
        "title": file_path.stem,
        "page": 1,
        "section": "page 1",
        "url": None,
        "text": text,
        "source_path": str(file_path),
        **metadata,
    }


def iter_corpus_pages(corpus_path: Path) -> Iterator[dict]:
    if not corpus_path.exists() or not corpus_path.is_dir():
        return

    for file_path in sorted(corpus_path.iterdir()):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            yield from load_pdf_pages(file_path)
        elif suffix in {".txt", ".md"}:
            yield from load_text_document(file_path)
