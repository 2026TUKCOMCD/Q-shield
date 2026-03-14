from __future__ import annotations

from typing import Any

from app.config import AI_VECTOR_COLLECTION, AI_VECTOR_DB_DIR

try:
    import chromadb
except Exception:  # pragma: no cover - optional dependency in tests
    chromadb = None


DEFAULT_COLLECTION_NAME = AI_VECTOR_COLLECTION


class VectorStoreError(RuntimeError):
    pass


class VectorStore:
    def __init__(
        self,
        *,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_dir: str | None = None,
    ) -> None:
        if chromadb is None:
            raise VectorStoreError("chromadb package is not installed")
        self._collection_name = collection_name
        self._persist_dir = persist_dir or AI_VECTOR_DB_DIR
        self.client = chromadb.PersistentClient(path=self._persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self.client.delete_collection(self._collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("chunks and embeddings length mismatch")
        if not chunks:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        filtered_embeddings: list[list[float]] = []

        for chunk, embedding in zip(chunks, embeddings):
            if not embedding:
                continue
            ids.append(str(chunk.get("chunk_id") or f"{chunk.get('doc_id')}::{chunk.get('page')}::{len(ids)}"))
            documents.append(str(chunk.get("text") or ""))
            filtered_embeddings.append(embedding)
            metadatas.append(
                {
                    "doc_id": chunk.get("doc_id"),
                    "title": chunk.get("title"),
                    "page": chunk.get("page"),
                    "section": chunk.get("section"),
                    "url": chunk.get("url"),
                    "source_path": chunk.get("source_path"),
                }
            )

        if not ids:
            return

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=filtered_embeddings,
        )

    def query(self, query_embedding: list[float], *, top_k: int = 6) -> list[dict[str, Any]]:
        if not query_embedding:
            return []
        result = self.collection.query(query_embeddings=[query_embedding], n_results=max(1, int(top_k)))

        docs = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        rows: list[dict[str, Any]] = []
        for index, (doc, metadata) in enumerate(zip(docs, metadatas)):
            meta = metadata or {}
            distance = None
            if isinstance(distances, list) and index < len(distances):
                distance = distances[index]
            rows.append(
                {
                    "text": str(doc or ""),
                    "doc_id": str(meta.get("doc_id") or "unknown"),
                    "title": str(meta.get("title") or "Unknown"),
                    "section": str(meta.get("section") or "N/A"),
                    "page": int(meta["page"]) if meta.get("page") is not None else None,
                    "url": meta.get("url"),
                    "source_path": meta.get("source_path"),
                    "distance": distance,
                }
            )
        return rows

    def count(self) -> int:
        return int(self.collection.count())

    @property
    def collection_name(self) -> str:
        return self._collection_name
