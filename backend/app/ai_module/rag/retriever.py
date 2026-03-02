from __future__ import annotations

import re

from app.ai_module.rag.indexer import build_or_load_index
from app.ai_module.schemas import Citation


def _tokenize(value: str) -> set[str]:
    return set(token for token in re.findall(r"[a-z0-9\-]+", value.lower()) if len(token) > 1)


def retrieve_citations(query: str, *, top_k: int = 3, corpus_path: str | None = None) -> list[Citation]:
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
