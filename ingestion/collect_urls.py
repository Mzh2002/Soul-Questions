"""Collect seed URLs for Souls-like game wiki pages.

Generates a manifest of URLs to scrape, organized by game and category.
Respects robots.txt by checking before adding each domain.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

# Fextralife wiki base paths per game
FEXTRALIFE_GAMES: dict[str, str] = {
    "Dark Souls": "https://darksouls.wiki.fextralife.com",
    "Dark Souls 2": "https://darksouls2.wiki.fextralife.com",
    "Dark Souls 3": "https://darksouls3.wiki.fextralife.com",
    "Elden Ring": "https://eldenring.wiki.fextralife.com",
    "Bloodborne": "https://bloodborne.wiki.fextralife.com",
    "Sekiro": "https://sekiroshadowsdietwice.wiki.fextralife.com",
    "Demon's Souls": "https://demonssouls.wiki.fextralife.com",
}

# Key category hub pages on Fextralife wikis
CATEGORY_PATHS: dict[str, list[str]] = {
    "boss": ["/Bosses"],
    "item": ["/Items", "/Weapons", "/Armor", "/Rings", "/Shields"],
    "npc": ["/NPCs"],
    "location": ["/Locations", "/Maps"],
    "quest": ["/Quests", "/Side+Quests"],
    "lore": ["/Lore"],
    "mechanic": ["/Game+Mechanics", "/Stats", "/Combat"],
    "build": ["/Builds", "/Character+Builds"],
}


def check_robots(base_url: str, user_agent: str = "*") -> bool:
    """Return True if the base URL allows crawling for the given user-agent."""
    rp = RobotFileParser()
    robots_url = f"{base_url}/robots.txt"
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, base_url + "/")
    except Exception:
        logger.warning("Could not fetch robots.txt for %s, skipping", base_url)
        return False


def discover_links_from_hub(hub_url: str, base_url: str) -> list[str]:
    """Fetch a hub page and extract internal wiki links."""
    try:
        resp = requests.get(hub_url, timeout=15, headers={"User-Agent": "SoulQuestionsBot/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", hub_url, exc)
        return []

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "lxml")
    links: list[str] = []
    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        if href.startswith("/") and not href.startswith("//"):
            full = base_url + href
        elif href.startswith(base_url):
            full = href
        else:
            continue
        if full not in links:
            links.append(full)
    return links


def collect_urls(
    output_path: str | Path = "data/url_manifest.json",
    max_per_category: int = 30,
) -> Path:
    """Build and save a URL manifest for all games and categories.

    Args:
        output_path: Where to write the JSON manifest.
        max_per_category: Maximum links per category per game.

    Returns:
        Path to the saved manifest file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []

    for game, base_url in FEXTRALIFE_GAMES.items():
        if not check_robots(base_url):
            logger.info("Skipping %s — robots.txt disallows", game)
            continue

        logger.info("Collecting URLs for %s", game)

        for category, paths in CATEGORY_PATHS.items():
            for path in paths:
                hub_url = base_url + path
                links = discover_links_from_hub(hub_url, base_url)
                for link in links[:max_per_category]:
                    entry = {
                        "url": link,
                        "game": game,
                        "category": category,
                        "hub_page": hub_url,
                    }
                    if entry not in manifest:
                        manifest.append(entry)

    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Saved %d URLs to %s", len(manifest), output_path)
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collect_urls()
