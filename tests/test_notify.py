import pytest

from portfolio_monitor.config import NotifyConfig
from portfolio_monitor import notify as notify_module


def make_config(**overrides):
    base = dict(
        smtp_host="",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        email_from="",
        email_to="",
        slack_webhook_url="",
        discord_webhook_url="",
        telegram_bot_token="",
        telegram_chat_id="",
    )
    base.update(overrides)
    return NotifyConfig(**base)


def test_notify_raises_when_nothing_configured():
    with pytest.raises(RuntimeError, match="No notification channel"):
        notify_module.notify("subj", "body", make_config())


def test_notify_sends_to_all_configured_channels(monkeypatch):
    calls = []
    monkeypatch.setattr(notify_module, "send_email", lambda s, b, c: calls.append("email"))
    monkeypatch.setattr(notify_module, "send_slack", lambda s, b, c: calls.append("slack"))
    monkeypatch.setattr(notify_module, "_CHANNELS", (
        ("email", notify_module.send_email, lambda c: True),
        ("slack", notify_module.send_slack, lambda c: True),
        ("discord", notify_module.send_discord, lambda c: False),
    ))

    sent = notify_module.notify("subj", "body", make_config())

    assert sent == ["email", "slack"]
    assert calls == ["email", "slack"]


def test_notify_continues_after_one_channel_fails(monkeypatch):
    def failing_send(subject, body, config):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notify_module, "_CHANNELS", (
        ("email", failing_send, lambda c: True),
        ("slack", lambda s, b, c: None, lambda c: True),
    ))

    sent = notify_module.notify("subj", "body", make_config())

    assert sent == ["slack"]


def test_notify_raises_when_all_configured_channels_fail(monkeypatch):
    def failing_send(subject, body, config):
        raise RuntimeError("down")

    monkeypatch.setattr(notify_module, "_CHANNELS", (
        ("email", failing_send, lambda c: True),
    ))

    with pytest.raises(RuntimeError, match="All configured notification channels failed"):
        notify_module.notify("subj", "body", make_config())


def test_telegram_only_config_is_recognized(monkeypatch):
    calls = []
    monkeypatch.setattr(notify_module, "send_telegram", lambda s, b, c: calls.append("telegram"))
    monkeypatch.setattr(
        notify_module,
        "_CHANNELS",
        tuple(
            (name, notify_module.send_telegram if name == "telegram" else send, is_configured)
            for name, send, is_configured in notify_module._CHANNELS
        ),
    )
    config = make_config(telegram_bot_token="tok", telegram_chat_id="123")

    sent = notify_module.notify("subj", "body", config)

    assert sent == ["telegram"]
    assert calls == ["telegram"]


def test_send_telegram_requires_token_and_chat_id():
    with pytest.raises(RuntimeError, match="Telegram notification is not configured"):
        notify_module.send_telegram("subj", "body", make_config())
