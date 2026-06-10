"""Tests for the citation module."""

from rag.citations import extract_cited_sources, format_context_for_prompt


def test_format_context_empty():
    assert "(No relevant sources found)" in format_context_for_prompt([])


def test_format_context_with_chunks():
    chunks = [
        {"text": "Boss info", "title": "Nameless King", "game": "Dark Souls 3", "source_url": "http://example.com"},
        {"text": "Lore text", "title": "Gwyn", "game": "Dark Souls", "source_url": ""},
    ]
    result = format_context_for_prompt(chunks)
    assert "[Source 1]" in result
    assert "[Source 2]" in result
    assert "Nameless King" in result
    assert "Dark Souls 3" in result


def test_extract_cited_sources():
    chunks = [
        {"title": "A", "source_url": "http://a.com", "game": "DS1", "category": "boss", "text": "chunk a text"},
        {"title": "B", "source_url": "http://b.com", "game": "DS3", "category": "lore", "text": "chunk b text"},
        {"title": "C", "source_url": "http://c.com", "game": "ER", "category": "item", "text": "chunk c text"},
    ]
    answer = "According to [Source 1], the boss is tough. Also see [Source 3]."
    cited = extract_cited_sources(answer, chunks)
    assert len(cited) == 2
    assert cited[0]["title"] == "A"
    assert cited[1]["title"] == "C"


def test_extract_no_citations():
    chunks = [{"title": "A", "source_url": "", "game": "", "category": "", "text": "x"}]
    cited = extract_cited_sources("No sources used here.", chunks)
    assert len(cited) == 0
