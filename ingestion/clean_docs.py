"""Clean raw HTML documents into plain-text with metadata."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

NOISE_SELECTORS = [
    "nav", "header", "footer", "aside", ".sidebar", ".ad", ".advertisement",
    ".cookie-banner", ".social-share", "#comments", ".comments",
    "script", "style", "noscript", ".wiki-sidebar", ".page-header",
    ".infobox-bonfire", ".wiki-video",
]


def extract_text(html: str) -> str:
    """Remove boilerplate and extract useful text from wiki HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Remove comment nodes
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove noise elements
    for selector in NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    # Try to get main content area
    main = soup.select_one("#wiki-content-block, .wiki-content, #content, main, article")
    target = main if main else soup.body if soup.body else soup

    text = target.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove very short lines that are navigation remnants
    lines = [line for line in text.split("\n") if len(line.strip()) > 2]
    return "\n".join(lines)


def extract_title(html: str) -> str:
    """Extract the page title from HTML."""
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Remove common suffixes like "| Fextralife"
        for sep in ["|", " - ", " :: "]:
            if sep in title:
                title = title.split(sep)[0].strip()
        return title
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else "Untitled"


def clean_docs(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/processed",
) -> int:
    """Clean all raw HTML docs and save as structured JSON.

    Args:
        raw_dir: Directory containing raw scraped JSON files.
        output_dir: Directory to write cleaned documents.

    Returns:
        Number of documents cleaned.
    """
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned = 0
    for raw_file in sorted(raw_dir.glob("*.json")):
        try:
            raw = json.loads(raw_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping %s: %s", raw_file, exc)
            continue

        html = raw.get("html", "")
        if not html:
            continue

        text = extract_text(html)
        if len(text.strip()) < 50:
            logger.debug("Skipping %s — too little content", raw_file.name)
            continue

        title = extract_title(html)

        doc = {
            "id": raw_file.stem,
            "title": title,
            "text": text,
            "source_url": raw.get("url", ""),
            "game": raw.get("game", ""),
            "category": raw.get("category", ""),
            "date_collected": datetime.now(timezone.utc).isoformat(),
        }

        out_file = output_dir / raw_file.name
        out_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        cleaned += 1

    logger.info("Cleaned %d documents", cleaned)
    return cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clean_docs()
