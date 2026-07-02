from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import urlopen

import feedparser


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    link: str
    published: str | None


def fetch_news(feed_urls: list[str], limit_per_feed: int = 4) -> list[NewsItem]:
    items: list[NewsItem] = []
    for url in feed_urls:
        try:
            with urlopen(url, timeout=8) as response:
                feed = feedparser.parse(response.read())
        except (OSError, URLError):
            continue
        source = str(feed.feed.get("title", url))
        for entry in feed.entries[:limit_per_feed]:
            published = entry.get("published") or entry.get("updated")
            items.append(
                NewsItem(
                    title=str(entry.get("title", "")).strip(),
                    source=source,
                    link=str(entry.get("link", "")).strip(),
                    published=None if published is None else str(published),
                )
            )
    return [item for item in items if item.title]


def news_context(feed_urls: list[str]) -> dict[str, object]:
    return {
        "as_of_utc": datetime.now(UTC).isoformat(),
        "headlines": [item.__dict__ for item in fetch_news(feed_urls)],
    }
