"""Tests for the reranker module."""

from rag.reranker import rerank


def test_rerank_basic():
    chunks = [
        {"text": "The Nameless King is a boss in Dark Souls 3", "score": 0.8},
        {"text": "Estus Flask is a healing item", "score": 0.9},
        {"text": "Nameless King uses lightning attacks and rides a storm drake", "score": 0.7},
    ]
    result = rerank("Nameless King boss fight strategy", chunks, top_k=2)
    assert len(result) == 2
    # Chunks mentioning "nameless king" should rank higher
    assert "Nameless King" in result[0]["text"]


def test_rerank_empty():
    assert rerank("test", [], top_k=5) == []


def test_rerank_top_k():
    chunks = [{"text": f"chunk {i}", "score": 0.5} for i in range(10)]
    result = rerank("chunk", chunks, top_k=3)
    assert len(result) == 3
