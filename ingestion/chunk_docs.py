"""Chunk cleaned documents into RAG-ready pieces with metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by character count.

    Attempts to break at paragraph or sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to break at paragraph
            break_point = text.rfind("\n\n", start, end)
            if break_point == -1 or break_point <= start:
                # Try sentence boundary
                break_point = text.rfind(". ", start, end)
            if break_point == -1 or break_point <= start:
                break_point = end
            else:
                break_point += 1  # include the period or newline
        else:
            break_point = len(text)

        chunk = text[start:break_point].strip()
        if chunk:
            chunks.append(chunk)

        start = break_point - overlap if break_point - overlap > start else break_point

    return chunks


def chunk_docs(
    processed_dir: str | Path = "data/processed",
    output_path: str | Path = "data/chunks/chunks.jsonl",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Chunk all processed documents and save as JSONL.

    Args:
        processed_dir: Directory with cleaned JSON documents.
        output_path: Path for the output JSONL file.
        chunk_size: Maximum characters per chunk.
        overlap: Overlap between consecutive chunks.

    Returns:
        Total number of chunks created.
    """
    processed_dir = Path(processed_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for doc_file in sorted(processed_dir.glob("*.json")):
            try:
                doc = json.loads(doc_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping %s: %s", doc_file, exc)
                continue

            text = doc.get("text", "")
            if not text:
                continue

            chunks = chunk_text(text, chunk_size, overlap)
            for i, chunk in enumerate(chunks):
                record = {
                    "chunk_id": f"{doc['id']}_chunk_{i}",
                    "doc_id": doc.get("id", ""),
                    "text": chunk,
                    "title": doc.get("title", ""),
                    "source_url": doc.get("source_url", ""),
                    "game": doc.get("game", ""),
                    "category": doc.get("category", ""),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1

    logger.info("Created %d chunks from %s", total_chunks, processed_dir)
    return total_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    chunk_docs()
