"""Alert rules: price swings, volume spikes, and important news."""
from dataclasses import dataclass

from .config import AlertConfig
from .news import NewsItem
from .toss_client import Holding


@dataclass(frozen=True)
class Alert:
    ticker: str
    reason: str
    detail: str


def check_price_move(holding: Holding, config: AlertConfig) -> Alert | None:
    if abs(holding.change_pct) >= config.price_change_pct:
        direction = "up" if holding.change_pct > 0 else "down"
        return Alert(
            ticker=holding.ticker,
            reason="price_move",
            detail=f"{holding.name} is {direction} {holding.change_pct:+.2f}% today",
        )
    return None


def check_volume_spike(
    holding: Holding, avg_volume: float, config: AlertConfig
) -> Alert | None:
    if avg_volume > 0 and holding.volume >= avg_volume * config.volume_multiple:
        return Alert(
            ticker=holding.ticker,
            reason="volume_spike",
            detail=(
                f"{holding.name} volume {holding.volume:,} is "
                f"{holding.volume / avg_volume:.1f}x its average"
            ),
        )
    return None


def check_important_news(ticker: str, news_items: list[NewsItem]) -> list[Alert]:
    return [
        Alert(ticker=ticker, reason="important_news", detail=item.title)
        for item in news_items
        if item.is_important
    ]


def evaluate_holding(
    holding: Holding,
    news_items: list[NewsItem],
    config: AlertConfig,
    avg_volume: float = 0.0,
) -> list[Alert]:
    alerts = []
    if price_alert := check_price_move(holding, config):
        alerts.append(price_alert)
    if volume_alert := check_volume_spike(holding, avg_volume, config):
        alerts.append(volume_alert)
    alerts.extend(check_important_news(holding.ticker, news_items))
    return alerts
