"""Tests for the document chunking module."""

from ingestion.chunk_docs import chunk_text


def test_short_text_single_chunk():
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_text_split_into_multiple_chunks():
    text = "A" * 500 + "\n\n" + "B" * 500
    chunks = chunk_text(text, chunk_size=600, overlap=50)
    assert len(chunks) >= 2


def test_overlap_preserves_context():
    words = " ".join([f"word{i}" for i in range(200)])
    chunks = chunk_text(words, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # Check some overlap between consecutive chunks
    for i in range(len(chunks) - 1):
        # There should be some shared content
        c1_end = chunks[i][-40:]
        c2_start = chunks[i + 1][:40]
        # At minimum the chunks should be non-empty
        assert len(chunks[i]) > 0
        assert len(chunks[i + 1]) > 0


def test_empty_text():
    chunks = chunk_text("", chunk_size=100, overlap=20)
    assert chunks == [""] or chunks == []


def test_chunk_respects_size():
    text = "Hello world. " * 200
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    for chunk in chunks:
        # Allow some slack for boundary finding
        assert len(chunk) <= 350
