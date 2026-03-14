from __future__ import annotations

from pathlib import Path
from typing import Iterator

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency in tests
    PdfReader = None


def load_pdf_pages(pdf_path: Path) -> Iterator[dict]:
    if PdfReader is None:
        return
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return

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
        }


def load_text_document(file_path: Path) -> Iterator[dict]:
    try:
        text = file_path.read_text(encoding="utf-8").strip()
    except Exception:
        return

    if not text:
        return

    yield {
        "doc_id": file_path.name,
        "title": file_path.stem,
        "page": 1,
        "section": "page 1",
        "url": None,
        "text": text,
        "source_path": str(file_path),
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
