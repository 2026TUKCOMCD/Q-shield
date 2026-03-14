from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in tests
    OpenAI = None


class EmbeddingsError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _get_client() -> Any:
    if OpenAI is None:
        raise EmbeddingsError("openai package is not installed")
    if not OPENAI_API_KEY:
        raise EmbeddingsError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = _get_client()
    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=texts,
    )
    return [list(item.embedding) for item in response.data]
