from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.ai_module.rag.embeddings import EmbeddingsError, embed_texts
from app.ai_module.rag.indexer import build_or_load_index
from app.ai_module.rag.vector_store import VectorStore, VectorStoreError
from app.ai_module.schemas import Citation
from app.config import AI_RAG_CORPUS_PATH

logger = logging.getLogger(__name__)


def _tokenize(value: str) -> set[str]:
    return set(token for token in re.findall(r"[a-z0-9\-]+", value.lower()) if len(token) > 1)


class RetrievalError(RuntimeError):
    pass


@dataclass
class RagCorpusStatus:
    corpus_path: str
    corpus_exists: bool
    pdf_count: int = 0
    text_count: int = 0
    vector_store_collection: str | None = None
    vector_store_ready: bool = False
    vector_count: int = 0
    failure_reason: str | None = None

    @property
    def rag_corpus_loaded(self) -> bool:
        if self.vector_count > 0:
            return True
        return self.corpus_exists and (self.pdf_count + self.text_count) > 0

    def to_dict(self) -> dict:
        return {
            "corpus_path": self.corpus_path,
            "corpus_exists": self.corpus_exists,
            "pdf_count": self.pdf_count,
            "text_count": self.text_count,
            "vector_store_collection": self.vector_store_collection,
            "vector_store_ready": self.vector_store_ready,
            "vector_count": self.vector_count,
            "failure_reason": self.failure_reason,
            "rag_corpus_loaded": self.rag_corpus_loaded,
        }


@dataclass
class RetrievalResult:
    query_text: str
    top_k: int
    chunks: list[dict] = field(default_factory=list)
    vector_store_collection: str | None = None
    vector_count_before_query: int = 0
    failure_reason: str | None = None

    @property
    def success(self) -> bool:
        return self.failure_reason is None

    def to_dict(self) -> dict:
        return {
            "top_k": self.top_k,
            "retrieved_count": len(self.chunks),
            "vector_store_collection": self.vector_store_collection,
            "vector_count_before_query": self.vector_count_before_query,
            "failure_reason": self.failure_reason,
        }


def inspect_rag_corpus(corpus_path: str | None = None) -> RagCorpusStatus:
    raw_path = str(corpus_path or AI_RAG_CORPUS_PATH or "").strip()
    root = Path(raw_path).expanduser() if raw_path else None
    exists = bool(root and root.exists() and root.is_dir())
    pdf_count = 0
    text_count = 0
    if exists and root is not None:
        pdf_count = len(list(root.glob("*.pdf")))
        text_count = len(list(root.glob("*.txt"))) + len(list(root.glob("*.md")))

    status = RagCorpusStatus(
        corpus_path=str(root) if root else "",
        corpus_exists=exists,
        pdf_count=pdf_count,
        text_count=text_count,
        failure_reason=None,
    )

    try:
        store = VectorStore()
        status.vector_store_collection = store.collection_name
        status.vector_store_ready = True
        status.vector_count = store.count()
    except VectorStoreError as exc:
        status.failure_reason = str(exc)

    if status.vector_count <= 0:
        if not raw_path:
            status.failure_reason = "AI_RAG_CORPUS_PATH is not configured and vector store is empty"
        elif not exists:
            status.failure_reason = f"Configured corpus path does not exist: {raw_path}"
        elif (pdf_count + text_count) <= 0:
            status.failure_reason = f"Corpus path has no supported files (.pdf/.txt/.md): {status.corpus_path}"
        else:
            status.failure_reason = "Vector store is empty. Run corpus ingest first."
    elif status.failure_reason:
        status.failure_reason = None

    logger.info("ai_rag.corpus status=%s", status.to_dict())
    return status


def retrieve_relevant_chunks_with_debug(query_text: str, *, top_k: int = 6) -> RetrievalResult:
    result = RetrievalResult(query_text=query_text, top_k=top_k)
    query = query_text.strip()
    if not query:
        result.failure_reason = "Retrieval query is empty"
        logger.warning("ai_rag.retrieve status=%s", result.to_dict())
        return result

    try:
        store = VectorStore()
        result.vector_store_collection = store.collection_name
        result.vector_count_before_query = store.count()
    except VectorStoreError as exc:
        result.failure_reason = f"Vector store unavailable: {exc}"
        logger.error("ai_rag.retrieve status=%s", result.to_dict())
        return result

    if result.vector_count_before_query <= 0:
        result.failure_reason = "Vector store collection is empty. Run corpus ingest first."
        logger.warning("ai_rag.retrieve status=%s", result.to_dict())
        return result

    try:
        query_embedding = embed_texts([query])[0]
    except (EmbeddingsError, IndexError, ValueError) as exc:
        result.failure_reason = f"Embedding generation failed: {exc}"
        logger.error("ai_rag.retrieve status=%s", result.to_dict())
        return result

    try:
        result.chunks = store.query(query_embedding, top_k=top_k)
    except Exception as exc:
        result.failure_reason = f"Vector query failed: {exc}"
        logger.error("ai_rag.retrieve status=%s", result.to_dict())
        return result

    logger.info("ai_rag.retrieve status=%s", result.to_dict())
    return result


def retrieve_relevant_chunks(query_text: str, *, top_k: int = 6, raise_on_error: bool = False) -> list[dict]:
    result = retrieve_relevant_chunks_with_debug(query_text, top_k=top_k)
    if raise_on_error and result.failure_reason:
        raise RetrievalError(result.failure_reason)
    return result.chunks


def _retrieve_legacy_citations(query: str, *, top_k: int = 3, corpus_path: str | None = None) -> list[Citation]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    ranked: list[tuple[int, int, dict]] = []
    for chunk in build_or_load_index(corpus_path):
        search_text = str(chunk.get("search_text") or "")
        overlap = sum(1 for token in query_tokens if token in search_text)
        if overlap <= 0:
            continue
        ranked.append((overlap, len(search_text), chunk))

    ranked.sort(key=lambda item: (-item[0], item[1]))

    citations: list[Citation] = []
    for _, _, chunk in ranked[:top_k]:
        citations.append(
            Citation(
                doc_id=str(chunk.get("doc_id") or "unknown"),
                title=str(chunk.get("title") or "Unknown"),
                section=str(chunk.get("section") or "N/A"),
                page=int(chunk["page"]) if chunk.get("page") is not None else None,
                url=chunk.get("url"),
                snippet=str(chunk.get("snippet") or ""),
            )
        )
    return citations


def retrieve_citations(query: str, *, top_k: int = 3, corpus_path: str | None = None) -> list[Citation]:
    result = retrieve_relevant_chunks_with_debug(query, top_k=top_k)
    if result.chunks:
        citations: list[Citation] = []
        for chunk in result.chunks:
            citations.append(
                Citation(
                    doc_id=str(chunk.get("doc_id") or "unknown"),
                    title=str(chunk.get("title") or "Unknown"),
                    section=str(chunk.get("section") or "N/A"),
                    page=int(chunk["page"]) if chunk.get("page") is not None else None,
                    url=chunk.get("url"),
                    snippet=str(chunk.get("text") or ""),
                )
            )
        return citations

    if result.failure_reason:
        logger.warning("ai_rag.retrieve_citations fallback=legacy reason=%s", result.failure_reason)
    return _retrieve_legacy_citations(query, top_k=top_k, corpus_path=corpus_path)
