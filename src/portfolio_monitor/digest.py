"""Build a periodic news digest across all portfolio holdings."""
from .news import NewsItem, fetch_news
from .toss_client import Holding


def build_digest(holdings: list[Holding]) -> str:
    sections = []
    for holding in holdings:
        items = fetch_news(holding.ticker, holding.name)
        sections.append(_format_section(holding, items))
    if not sections:
        return "No holdings found."
    return "\n\n".join(sections)


def _format_section(holding: Holding, items: list[NewsItem]) -> str:
    header = f"{holding.name} ({holding.ticker}) — {holding.change_pct:+.2f}%"
    if not items:
        return f"{header}\nNo recent news."
    lines = [f"- {item.title}\n  {item.link}" for item in items]
    return header + "\n" + "\n".join(lines)
