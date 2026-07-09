"""Entry point for the portfolio-alert-monitor routine (hourly)."""
from datetime import datetime

from .alerts import Alert, evaluate_holding
from .config import AlertConfig, NotifyConfig, TossConfig
from .news import fetch_news
from .notify import send_email
from .toss_client import TossClient


def _volume_stats(toss: TossClient, ticker: str, lookback_days: int = 15) -> tuple[float, float]:
    """(current_volume, avg_volume) from daily candles. avg excludes today's candle."""
    candles = toss.get_daily_candles(ticker, count=lookback_days)
    if not candles:
        return 0.0, 0.0
    current_volume = candles[0].volume
    history = candles[1:]
    avg_volume = sum(c.volume for c in history) / len(history) if history else 0.0
    return current_volume, avg_volume


def collect_alerts() -> list[Alert]:
    toss = TossClient(TossConfig.from_env())
    alert_config = AlertConfig.from_env()
    holdings = toss.get_holdings()
    alerts: list[Alert] = []
    for holding in holdings:
        news_items = fetch_news(holding.ticker, holding.name, limit=5)
        current_volume, avg_volume = _volume_stats(toss, holding.ticker)
        alerts.extend(
            evaluate_holding(holding, news_items, alert_config, current_volume, avg_volume)
        )
    return alerts


def main() -> None:
    alerts = collect_alerts()
    if not alerts:
        print("No alerts triggered.")
        return
    subject = f"Portfolio alert — {datetime.now():%Y-%m-%d %H:%M} ({len(alerts)})"
    body = "\n".join(f"[{a.reason}] {a.ticker}: {a.detail}" for a in alerts)
    send_email(subject, body, NotifyConfig.from_env())
    print(subject)
    print(body)


if __name__ == "__main__":
    main()
