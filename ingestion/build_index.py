"""Build or update the vector store index from chunked documents."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_settings() -> tuple[str, str, str, Path]:
    """Load settings without requiring full Django if possible."""
    try:
        import django
        import os
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souls_rag.settings")
        django.setup()
        from django.conf import settings
        return (
            settings.EMBEDDING_PROVIDER,
            settings.EMBEDDING_MODEL,
            settings.VECTOR_STORE,
            settings.VECTORSTORE_DIR,
        )
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        return (
            os.getenv("EMBEDDING_PROVIDER", "sentence-transformers"),
            os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            os.getenv("VECTOR_STORE", "chroma"),
            Path(os.getenv("VECTORSTORE_DIR", "data/vectorstore")),
        )


def build_index(
    chunks_path: str | Path = "data/chunks/chunks.jsonl",
    rebuild: bool = False,
) -> int:
    """Build the vector index from chunks.

    Args:
        chunks_path: Path to the JSONL chunks file.
        rebuild: If True, wipe and rebuild the entire index.

    Returns:
        Number of chunks indexed.
    """
    # Import here to avoid heavy imports at module level
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from rag.embeddings import get_embedding_function

    emb_provider, emb_model, store_type, store_dir = _get_settings()
    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = Path(chunks_path)
    if not chunks_path.exists():
        logger.error("Chunks file not found: %s", chunks_path)
        return 0

    # Load chunks
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            texts.append(rec["text"])
            metadatas.append({
                "title": rec.get("title", ""),
                "source_url": rec.get("source_url", ""),
                "game": rec.get("game", ""),
                "category": rec.get("category", ""),
                "chunk_index": rec.get("chunk_index", 0),
                "doc_id": rec.get("doc_id", ""),
            })
            ids.append(rec["chunk_id"])

    if not texts:
        logger.warning("No chunks to index")
        return 0

    embed_fn = get_embedding_function(emb_provider, emb_model)

    if store_type == "chroma":
        return _build_chroma(texts, metadatas, ids, embed_fn, store_dir, rebuild)
    elif store_type == "faiss":
        return _build_faiss(texts, metadatas, ids, embed_fn, store_dir, rebuild)
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")


def _build_chroma(
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
    embed_fn,
    store_dir: Path,
    rebuild: bool,
) -> int:
    import chromadb

    client = chromadb.PersistentClient(path=str(store_dir / "chroma"))

    if rebuild:
        try:
            client.delete_collection("souls")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name="souls",
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_metas = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_embeddings = embed_fn(batch_texts)
        collection.upsert(
            documents=batch_texts,
            embeddings=batch_embeddings,
            metadatas=batch_metas,
            ids=batch_ids,
        )
        logger.info("Indexed batch %d–%d", i, i + len(batch_texts))

    logger.info("Chroma index built with %d vectors", collection.count())
    return collection.count()


def _build_faiss(
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
    embed_fn,
    store_dir: Path,
    rebuild: bool,
) -> int:
    import pickle

    import faiss
    import numpy as np

    faiss_dir = store_dir / "faiss"
    faiss_dir.mkdir(parents=True, exist_ok=True)
    index_path = faiss_dir / "index.faiss"
    meta_path = faiss_dir / "metadata.pkl"

    all_embeddings = embed_fn(texts)
    embeddings_array = np.array(all_embeddings, dtype="float32")

    dim = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dim)
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings_array)
    index.add(embeddings_array)

    faiss.write_index(index, str(index_path))

    meta_store = {
        "ids": ids,
        "texts": texts,
        "metadatas": metadatas,
    }
    with open(meta_path, "wb") as f:
        pickle.dump(meta_store, f)

    logger.info("FAISS index built with %d vectors (dim=%d)", index.ntotal, dim)
    return index.ntotal


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(description="Build vector index")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    parser.add_argument("--chunks", default="data/chunks/chunks.jsonl")
    args = parser.parse_args()
    build_index(args.chunks, rebuild=args.rebuild)
