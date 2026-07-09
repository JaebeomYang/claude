"""Notification delivery for digests and alerts: email, Slack, Discord."""
import smtplib
from email.mime.text import MIMEText

import requests

from .config import NotifyConfig


def send_email(subject: str, body: str, config: NotifyConfig) -> None:
    if not (config.smtp_host and config.email_from and config.email_to):
        raise RuntimeError(
            "Email notification is not configured (SMTP_HOST/NOTIFY_EMAIL_FROM/"
            "NOTIFY_EMAIL_TO missing)."
        )
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = config.email_from
    message["To"] = config.email_to

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        server.starttls()
        if config.smtp_username:
            server.login(config.smtp_username, config.smtp_password)
        server.sendmail(config.email_from, [config.email_to], message.as_string())


def send_slack(subject: str, body: str, config: NotifyConfig) -> None:
    if not config.slack_webhook_url:
        raise RuntimeError("Slack notification is not configured (SLACK_WEBHOOK_URL missing).")
    resp = requests.post(
        config.slack_webhook_url, json={"text": f"*{subject}*\n{body}"}, timeout=10
    )
    resp.raise_for_status()


def send_discord(subject: str, body: str, config: NotifyConfig) -> None:
    if not config.discord_webhook_url:
        raise RuntimeError(
            "Discord notification is not configured (DISCORD_WEBHOOK_URL missing)."
        )
    resp = requests.post(
        config.discord_webhook_url, json={"content": f"**{subject}**\n{body}"}, timeout=10
    )
    resp.raise_for_status()


_CHANNELS = (
    ("email", send_email, lambda c: bool(c.smtp_host and c.email_from and c.email_to)),
    ("slack", send_slack, lambda c: bool(c.slack_webhook_url)),
    ("discord", send_discord, lambda c: bool(c.discord_webhook_url)),
)


def notify(subject: str, body: str, config: NotifyConfig) -> list[str]:
    """Send to every configured channel. Returns the names of channels that succeeded.

    Raises RuntimeError only if no channel is configured at all, or every
    configured channel failed to send.
    """
    configured = [(name, send) for name, send, is_configured in _CHANNELS if is_configured(config)]
    if not configured:
        raise RuntimeError(
            "No notification channel is configured (set SMTP_*/NOTIFY_EMAIL_*, "
            "SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL)."
        )

    sent = []
    errors = []
    for name, send in configured:
        try:
            send(subject, body, config)
            sent.append(name)
        except Exception as exc:
            # Keep trying the remaining channels instead of failing on the first one.
            errors.append(f"{name}: {exc}")

    if not sent:
        raise RuntimeError(f"All configured notification channels failed: {'; '.join(errors)}")
    return sent
