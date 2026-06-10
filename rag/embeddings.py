"""Configurable embedding functions for vector indexing and retrieval."""

from __future__ import annotations

from typing import Callable


def get_embedding_function(
    provider: str = "sentence-transformers",
    model_name: str = "all-MiniLM-L6-v2",
) -> Callable[[list[str]], list[list[float]]]:
    """Return an embedding function based on provider config.

    Args:
        provider: One of 'sentence-transformers' or 'openai'.
        model_name: Model identifier for the chosen provider.

    Returns:
        A callable that maps a list of strings to a list of embedding vectors.
    """
    if provider == "sentence-transformers":
        return _sentence_transformer_embedder(model_name)
    elif provider == "openai":
        return _openai_embedder(model_name)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


def _sentence_transformer_embedder(
    model_name: str,
) -> Callable[[list[str]], list[list[float]]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)

    def embed(texts: list[str]) -> list[list[float]]:
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    return embed


def _openai_embedder(
    model_name: str,
) -> Callable[[list[str]], list[list[float]]]:
    import os

    import openai

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    def embed(texts: list[str]) -> list[list[float]]:
        response = client.embeddings.create(input=texts, model=model_name)
        return [item.embedding for item in response.data]

    return embed
