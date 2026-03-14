from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterator

from app.ai_module.rag.embeddings import embed_texts
from app.ai_module.rag.loader import iter_corpus_pages
from app.ai_module.rag.vector_store import DEFAULT_COLLECTION_NAME, VectorStore
from app.config import AI_RAG_CORPUS_PATH

logger = logging.getLogger(__name__)


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    normalized = " ".join((text or "").split())
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be zero or positive")
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def _batched(items: list[dict], batch_size: int) -> Iterator[list[dict]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def ingest_corpus(
    *,
    corpus_path: str | None = None,
    chunk_size: int = 1200,
    overlap: int = 150,
    batch_size: int = 64,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    reset: bool = False,
) -> int:
    target_path = str(corpus_path or AI_RAG_CORPUS_PATH or "").strip()
    if not target_path:
        logger.warning("ai_rag.ingest status=skipped reason=no_corpus_path")
        return 0

    root = Path(target_path).expanduser()
    if not root.exists() or not root.is_dir():
        logger.warning("ai_rag.ingest status=skipped reason=missing_corpus_dir path=%s", str(root))
        return 0

    pdf_count = len(list(root.glob("*.pdf")))
    text_count = len(list(root.glob("*.txt"))) + len(list(root.glob("*.md")))
    logger.info(
        "ai_rag.ingest stage=corpus_detected path=%s pdf_count=%s text_count=%s",
        str(root),
        pdf_count,
        text_count,
    )

    chunks: list[dict] = []
    for page in iter_corpus_pages(root):
        page_chunks = chunk_text(str(page.get("text") or ""), chunk_size=chunk_size, overlap=overlap)
        for chunk_index, text in enumerate(page_chunks, start=1):
            chunks.append(
                {
                    "chunk_id": f"{page.get('doc_id')}::p{page.get('page')}::c{chunk_index}",
                    "doc_id": page.get("doc_id"),
                    "title": page.get("title"),
                    "page": page.get("page"),
                    "section": page.get("section"),
                    "url": page.get("url"),
                    "text": text,
                    "source_path": page.get("source_path"),
                }
            )

    if not chunks:
        logger.warning("ai_rag.ingest status=skipped reason=no_chunks_created path=%s", str(root))
        return 0

    store = VectorStore(collection_name=collection_name)
    if reset:
        store.reset()
        logger.info("ai_rag.ingest stage=vector_reset collection=%s", store.collection_name)

    safe_batch_size = max(1, int(batch_size))
    embedded_total = 0
    for batch in _batched(chunks, safe_batch_size):
        embeddings = embed_texts([str(item.get("text") or "") for item in batch])
        store.upsert_chunks(batch, embeddings)
        embedded_total += len(embeddings)
    logger.info(
        "ai_rag.ingest stage=completed chunks_created=%s embeddings_stored=%s collection=%s",
        len(chunks),
        embedded_total,
        store.collection_name,
    )
    return len(chunks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest AI RAG corpus into Chroma vector DB")
    parser.add_argument("--corpus-path", default=AI_RAG_CORPUS_PATH, help="Folder with .pdf/.txt/.md files")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=150)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--reset", action="store_true", help="Reset vector collection before ingest")
    args = parser.parse_args(argv)

    count = ingest_corpus(
        corpus_path=args.corpus_path,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        batch_size=args.batch_size,
        collection_name=args.collection_name,
        reset=args.reset,
    )
    print(f"Ingested {count} chunks")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
