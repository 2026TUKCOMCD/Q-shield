from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.config import AI_RAG_CACHE_PATH, AI_RAG_CORPUS_PATH


try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency at runtime
    PdfReader = None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _chunk_page_text(text: str, *, doc_id: str, title: str, page_number: int) -> list[dict]:
    cleaned = _normalize_text(text)
    if not cleaned:
        return []

    chunks: list[dict] = []
    max_chars = 900
    for index in range(0, len(cleaned), max_chars):
        snippet = cleaned[index : index + max_chars]
        if not snippet:
            continue
        chunks.append(
            {
                "doc_id": doc_id,
                "title": title,
                "section": f"page {page_number}",
                "page": page_number,
                "snippet": snippet,
                "search_text": snippet.lower(),
            }
        )
    return chunks


def _read_pdf_chunks(file_path: Path) -> list[dict]:
    if PdfReader is None:
        return []

    try:
        reader = PdfReader(str(file_path))
    except Exception:
        return []

    chunks: list[dict] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        chunks.extend(
            _chunk_page_text(
                page_text,
                doc_id=file_path.name,
                title=file_path.stem,
                page_number=page_index,
            )
        )
    return chunks


def _read_text_chunks(file_path: Path) -> list[dict]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return []
    return _chunk_page_text(text, doc_id=file_path.name, title=file_path.stem, page_number=1)


def _cache_path_for(corpus_path: str | None = None) -> Path | None:
    cache_path = AI_RAG_CACHE_PATH.strip() if AI_RAG_CACHE_PATH else ""
    if cache_path:
        return Path(cache_path)
    raw_path = str(corpus_path or AI_RAG_CORPUS_PATH or "").strip()
    if not raw_path:
        return None
    root = Path(raw_path).expanduser()
    return root / ".qshield_ai_rag_index.json"


def _load_cache(cache_path: Path) -> list[dict] | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, list):
        return data
    return None


def _save_cache(cache_path: Path, chunks: list[dict]) -> None:
    try:
        cache_path.write_text(json.dumps(chunks, ensure_ascii=True), encoding="utf-8")
    except Exception:
        return


@lru_cache(maxsize=4)
def build_or_load_index(corpus_path: str | None = None) -> list[dict]:
    raw_path = str(corpus_path or AI_RAG_CORPUS_PATH or "").strip()
    if not raw_path:
        return []

    root = Path(raw_path).expanduser()
    if not root.exists() or not root.is_dir():
        return []

    cache_path = _cache_path_for(str(root))
    if cache_path:
        cached = _load_cache(cache_path)
        if cached is not None:
            return cached

    chunks: list[dict] = []
    for file_path in sorted(root.iterdir()):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            chunks.extend(_read_pdf_chunks(file_path))
        elif suffix in {".txt", ".md"}:
            chunks.extend(_read_text_chunks(file_path))

    if cache_path and chunks:
        _save_cache(cache_path, chunks)
    return chunks


def main() -> int:
    chunks = build_or_load_index()
    print(f"Indexed {len(chunks)} chunks")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
