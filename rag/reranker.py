"""Simple reranking of retrieved chunks based on keyword overlap."""

from __future__ import annotations

import re


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Re-score chunks using keyword overlap + original vector score.

    This is a lightweight reranker. For production, swap in a cross-encoder
    model (e.g., cross-encoder/ms-marco-MiniLM-L-6-v2).

    Args:
        query: Original user query.
        chunks: Retrieved chunks with 'text' and 'score' keys.
        top_k: Number of chunks to return after reranking.

    Returns:
        Top-k chunks sorted by combined score.
    """
    query_tokens = set(_tokenize(query))

    scored: list[tuple[float, dict]] = []
    for chunk in chunks:
        chunk_tokens = set(_tokenize(chunk["text"]))
        if not query_tokens:
            overlap = 0.0
        else:
            overlap = len(query_tokens & chunk_tokens) / len(query_tokens)
        combined = 0.6 * chunk.get("score", 0.0) + 0.4 * overlap
        scored.append((combined, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk in scored[:top_k]:
        chunk["score"] = score
        results.append(chunk)
    return results


def _tokenize(text: str) -> list[str]:
    """Simple lowercased word tokenization."""
    return re.findall(r"\b\w+\b", text.lower())
