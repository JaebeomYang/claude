from datetime import datetime, timezone

from portfolio_monitor.alerts import (
    check_important_news,
    check_price_move,
    check_volume_spike,
    evaluate_holding,
)
from portfolio_monitor.config import AlertConfig
from portfolio_monitor.news import NewsItem
from portfolio_monitor.toss_client import Holding

CONFIG = AlertConfig(price_change_pct=3.0, volume_multiple=2.0)


def make_holding(change_pct=0.0):
    return Holding(
        ticker="AAPL",
        name="Apple",
        market_country="US",
        currency="USD",
        quantity=10,
        last_price=100,
        avg_price=90,
        change_pct=change_pct,
        profit_loss_rate=11.1,
    )


def test_price_move_triggers_above_threshold():
    alert = check_price_move(make_holding(change_pct=3.5), CONFIG)
    assert alert is not None
    assert alert.reason == "price_move"


def test_price_move_triggers_on_drop():
    alert = check_price_move(make_holding(change_pct=-4.0), CONFIG)
    assert alert is not None


def test_price_move_no_alert_below_threshold():
    assert check_price_move(make_holding(change_pct=1.0), CONFIG) is None


def test_volume_spike_triggers():
    alert = check_volume_spike(make_holding(), 3000, avg_volume=1000, config=CONFIG)
    assert alert is not None
    assert alert.reason == "volume_spike"


def test_volume_spike_no_alert_when_normal():
    assert check_volume_spike(make_holding(), 1500, avg_volume=1000, config=CONFIG) is None


def test_volume_spike_ignored_when_no_baseline():
    assert check_volume_spike(make_holding(), 5000, avg_volume=0, config=CONFIG) is None


def test_important_news_filters_non_matching():
    items = [
        NewsItem("AAPL", "Apple releases new earnings guidance", "u1", datetime.now(timezone.utc), True),
        NewsItem("AAPL", "Apple store opens downtown", "u2", datetime.now(timezone.utc), False),
    ]
    alerts = check_important_news("AAPL", items)
    assert len(alerts) == 1
    assert alerts[0].detail == items[0].title


def test_evaluate_holding_combines_all_checks():
    holding = make_holding(change_pct=5.0)
    items = [
        NewsItem("AAPL", "Apple CEO to resign", "u1", datetime.now(timezone.utc), True),
    ]
    alerts = evaluate_holding(
        holding, items, CONFIG, current_volume=4000, avg_volume=1000
    )
    reasons = {a.reason for a in alerts}
    assert reasons == {"price_move", "volume_spike", "important_news"}
