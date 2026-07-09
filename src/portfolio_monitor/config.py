"""Environment-backed configuration. No secrets are ever hardcoded here."""
import os
from dataclasses import dataclass


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


@dataclass(frozen=True)
class TossConfig:
    base_url: str
    client_id: str
    client_secret: str
    access_token: str

    @classmethod
    def from_env(cls) -> "TossConfig":
        return cls(
            base_url=os.environ.get("TOSS_API_BASE_URL", "https://openapi.tossinvest.com"),
            client_id=os.environ.get("TOSS_CLIENT_ID", ""),
            client_secret=os.environ.get("TOSS_CLIENT_SECRET", ""),
            access_token=os.environ.get("TOSS_ACCESS_TOKEN", ""),
        )


@dataclass(frozen=True)
class AlertConfig:
    price_change_pct: float
    volume_multiple: float

    @classmethod
    def from_env(cls) -> "AlertConfig":
        return cls(
            price_change_pct=_float_env("ALERT_PRICE_CHANGE_PCT", 3.0),
            volume_multiple=_float_env("ALERT_VOLUME_MULTIPLE", 2.0),
        )


@dataclass(frozen=True)
class NotifyConfig:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: str
    slack_webhook_url: str
    discord_webhook_url: str

    @classmethod
    def from_env(cls) -> "NotifyConfig":
        return cls(
            smtp_host=os.environ.get("SMTP_HOST", ""),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_username=os.environ.get("SMTP_USERNAME", ""),
            smtp_password=os.environ.get("SMTP_PASSWORD", ""),
            email_from=os.environ.get("NOTIFY_EMAIL_FROM", ""),
            email_to=os.environ.get("NOTIFY_EMAIL_TO", ""),
            slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL", ""),
            discord_webhook_url=os.environ.get("DISCORD_WEBHOOK_URL", ""),
        )
