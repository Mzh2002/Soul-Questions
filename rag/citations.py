"""Format source citations for display."""

from __future__ import annotations


def format_context_for_prompt(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered source block for the LLM prompt.

    Args:
        chunks: List of chunk dicts with text, title, source_url, game.

    Returns:
        Formatted string with numbered sources.
    """
    if not chunks:
        return "(No relevant sources found)"

    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}]"
        if chunk.get("title"):
            header += f" {chunk['title']}"
        if chunk.get("game"):
            header += f" ({chunk['game']})"
        parts.append(f"{header}\n{chunk['text']}")
    return "\n\n".join(parts)


def extract_cited_sources(
    answer: str, chunks: list[dict]
) -> list[dict]:
    """Extract which sources were actually cited in the answer.

    Looks for [Source N] patterns in the answer text.

    Args:
        answer: The LLM's response text.
        chunks: The original retrieved chunks (1-indexed).

    Returns:
        List of cited source dicts.
    """
    import re

    cited_indices: set[int] = set()
    for match in re.finditer(r"\[Source\s+(\d+)\]", answer):
        cited_indices.add(int(match.group(1)))

    cited: list[dict] = []
    for i, chunk in enumerate(chunks, 1):
        if i in cited_indices:
            cited.append({
                "index": i,
                "title": chunk.get("title", ""),
                "url": chunk.get("source_url", ""),
                "game": chunk.get("game", ""),
                "category": chunk.get("category", ""),
                "snippet": chunk.get("text", "")[:200],
            })
    return cited
