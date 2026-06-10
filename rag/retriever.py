"""Retrieve relevant chunks from the vector store."""

from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

from .embeddings import get_embedding_function

logger = logging.getLogger(__name__)


def _resolve_settings() -> tuple[str, str, str, Path]:
    try:
        from django.conf import settings
        return (
            settings.EMBEDDING_PROVIDER,
            settings.EMBEDDING_MODEL,
            settings.VECTOR_STORE,
            settings.VECTORSTORE_DIR,
        )
    except Exception:
        return (
            os.getenv("EMBEDDING_PROVIDER", "sentence-transformers"),
            os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            os.getenv("VECTOR_STORE", "chroma"),
            Path(os.getenv("VECTORSTORE_DIR", "data/vectorstore")),
        )


class Retriever:
    """Unified retriever interface for Chroma and FAISS."""

    def __init__(self) -> None:
        self.emb_provider, self.emb_model, self.store_type, self.store_dir = (
            _resolve_settings()
        )
        self.embed_fn = get_embedding_function(self.emb_provider, self.emb_model)
        self._store: Any = None

    def _ensure_store(self) -> None:
        if self._store is not None:
            return

        if self.store_type == "chroma":
            import chromadb
            client = chromadb.PersistentClient(
                path=str(Path(self.store_dir) / "chroma")
            )
            self._store = client.get_collection("souls")
        elif self.store_type == "faiss":
            import faiss
            import numpy as np
            faiss_dir = Path(self.store_dir) / "faiss"
            index = faiss.read_index(str(faiss_dir / "index.faiss"))
            with open(faiss_dir / "metadata.pkl", "rb") as f:
                meta = pickle.load(f)
            self._store = {"index": index, "meta": meta}
        else:
            raise ValueError(f"Unknown vector store: {self.store_type}")

    def retrieve(
        self, query: str, top_k: int = 8, game_filter: str | None = None
    ) -> list[dict]:
        """Retrieve top-k relevant chunks for a query.

        Args:
            query: The user's question.
            top_k: Number of chunks to return.
            game_filter: Optional game name to filter results.

        Returns:
            List of dicts with keys: text, title, source_url, game, category, score.
        """
        self._ensure_store()
        query_emb = self.embed_fn([query])

        if self.store_type == "chroma":
            return self._retrieve_chroma(query_emb, top_k, game_filter)
        else:
            return self._retrieve_faiss(query_emb, top_k, game_filter)

    def _retrieve_chroma(
        self, query_emb: list[list[float]], top_k: int, game_filter: str | None
    ) -> list[dict]:
        where_filter = {"game": game_filter} if game_filter else None
        results = self._store.query(
            query_embeddings=query_emb,
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        items: list[dict] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({
                "text": doc,
                "title": meta.get("title", ""),
                "source_url": meta.get("source_url", ""),
                "game": meta.get("game", ""),
                "category": meta.get("category", ""),
                "score": 1 - dist,  # chroma returns distance; convert to similarity
            })
        return items

    def _retrieve_faiss(
        self, query_emb: list[list[float]], top_k: int, game_filter: str | None
    ) -> list[dict]:
        import faiss
        import numpy as np

        store = self._store
        index = store["index"]
        meta = store["meta"]

        query_array = np.array(query_emb, dtype="float32")
        faiss.normalize_L2(query_array)
        scores, indices = index.search(query_array, top_k * 3 if game_filter else top_k)

        items: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            m = meta["metadatas"][idx]
            if game_filter and m.get("game", "") != game_filter:
                continue
            items.append({
                "text": meta["texts"][idx],
                "title": m.get("title", ""),
                "source_url": m.get("source_url", ""),
                "game": m.get("game", ""),
                "category": m.get("category", ""),
                "score": float(score),
            })
            if len(items) >= top_k:
                break

        return items
