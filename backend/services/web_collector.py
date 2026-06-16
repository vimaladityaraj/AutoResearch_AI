from __future__ import annotations

import re
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from backend.core.config import get_settings

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 AutoResearchAI/1.0"
    )
}


class WebCollector:
    """Collects and extracts readable text from user-provided and seed web sources."""

    def __init__(self) -> None:
        self.cfg = get_settings()

    def build_seed_sources(self, company: str, extra_sources: list[str]) -> list[str]:
        """Build a small source list from user-provided URLs plus a Wikipedia seed URL."""
        urls: list[str] = []

        for url in extra_sources:
            clean_url = url.strip()
            if clean_url.startswith(("http://", "https://")):
                urls.append(clean_url)

        wikipedia_slug = quote_plus(company.strip().replace(" ", "_"))
        urls.append(f"https://en.wikipedia.org/wiki/{wikipedia_slug}")

        seen: list[str] = []
        for url in urls:
            if url not in seen:
                seen.append(url)

        return seen[: self.cfg.max_sources]

    def fetch(self, url: str) -> dict:
        """Fetch a URL and return extracted text, metadata, and failure details."""
        try:
            response = requests.get(
                url,
                headers=_HEADERS,
                timeout=self.cfg.request_timeout_seconds,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()

            title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else urlparse(url).netloc
            )

            text = soup.get_text("\n")
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]+", " ", text).strip()

            return {
                "url": url,
                "title": title[:180],
                "text": text[:9000],
                "ok": True,
                "error": None,
            }

        except Exception as exc:
            logger.warning(f"Failed to fetch {url}: {exc}")
            return {
                "url": url,
                "title": urlparse(url).netloc or url,
                "text": "",
                "ok": False,
                "error": str(exc),
            }

    def collect(self, company: str, sources: list[str]) -> list[dict]:
        """Collect all available source documents."""
        return [self.fetch(url) for url in self.build_seed_sources(company, sources)]
