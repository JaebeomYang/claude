"""News lookup per ticker via Google News RSS (no API key required)."""
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

import feedparser

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

IMPORTANT_KEYWORDS = (
    "earnings",
    "guidance",
    "lawsuit",
    "recall",
    "merger",
    "acquisition",
    "bankruptcy",
    "sec investigation",
    "downgrade",
    "upgrade",
    "ceo",
    "resign",
    "delisting",
    "dividend",
)


@dataclass(frozen=True)
class NewsItem:
    ticker: str
    title: str
    link: str
    published: datetime
    is_important: bool


def _is_important(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in IMPORTANT_KEYWORDS)


def fetch_news(ticker: str, name: str, limit: int = 5) -> list[NewsItem]:
    query = quote(f'"{name}" OR "{ticker}" stock')
    feed = feedparser.parse(RSS_URL.format(query=query))
    items = []
    for entry in feed.entries[:limit]:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if getattr(
            entry, "published_parsed", None
        ) else datetime.now(timezone.utc)
        items.append(
            NewsItem(
                ticker=ticker,
                title=entry.title,
                link=entry.link,
                published=published,
                is_important=_is_important(entry.title),
            )
        )
    return items
