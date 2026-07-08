"""Email delivery for digests and alerts."""
import smtplib
from email.mime.text import MIMEText

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
