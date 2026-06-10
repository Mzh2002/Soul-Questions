"""Scrape pages from the URL manifest and save raw HTML.

Respects rate-limiting with delays between requests.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DEFAULT_DELAY = 2.0  # seconds between requests


def scrape_pages(
    manifest_path: str | Path = "data/url_manifest.json",
    output_dir: str | Path = "data/raw",
    delay: float = DEFAULT_DELAY,
) -> int:
    """Download pages listed in the manifest.

    Args:
        manifest_path: Path to the JSON manifest from collect_urls.
        output_dir: Directory to save raw HTML files.
        delay: Seconds to wait between requests.

    Returns:
        Number of pages successfully downloaded.
    """
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    downloaded = 0
    for entry in manifest:
        url = entry["url"]
        # deterministic filename from URL
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        out_file = output_dir / f"{url_hash}.json"

        if out_file.exists():
            logger.debug("Already downloaded: %s", url)
            downloaded += 1
            continue

        try:
            resp = requests.get(
                url, timeout=20, headers={"User-Agent": "SoulQuestionsBot/1.0"}
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed %s: %s", url, exc)
            continue

        doc = {
            "url": url,
            "game": entry.get("game", ""),
            "category": entry.get("category", ""),
            "html": resp.text,
            "status_code": resp.status_code,
        }
        out_file.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        downloaded += 1
        logger.info("Downloaded [%d]: %s", downloaded, url)
        time.sleep(delay)

    logger.info("Finished: %d / %d pages downloaded", downloaded, len(manifest))
    return downloaded


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_pages()
