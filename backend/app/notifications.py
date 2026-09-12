from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def send_email_alert(*, recipient: str | None, subject: str, body: str) -> bool:
    """Send SMTP mail when configured; never fail the mentoring transaction."""
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM_EMAIL") or os.getenv("SMTP_USERNAME")
    if not host or not sender or not recipient:
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    timeout = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=timeout) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning("SMTP alert delivery failed: %s", exc)
        return False