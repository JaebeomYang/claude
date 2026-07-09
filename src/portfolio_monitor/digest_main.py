"""Entry point for the portfolio-news-digest routine (every 2 hours)."""
from datetime import datetime

from .config import NotifyConfig, TossConfig
from .digest import build_digest
from .notify import notify
from .toss_client import TossClient


def main() -> None:
    toss = TossClient(TossConfig.from_env())
    holdings = toss.get_holdings()
    body = build_digest(holdings)
    subject = f"Portfolio news digest — {datetime.now():%Y-%m-%d %H:%M}"
    sent = notify(subject, body, NotifyConfig.from_env())
    print(f"{subject} (sent via: {', '.join(sent)})")
    print(body)


if __name__ == "__main__":
    main()
