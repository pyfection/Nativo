"""
Outbound email with two backends behind one call (same pattern as
file_storage):

- **SMTP** (production): set SMTP_HOST (+ optionally SMTP_PORT,
  SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM). STARTTLS is attempted when the
  server supports it. Any transactional provider's SMTP endpoint works
  (Resend, Mailgun, SES, Postmark, ...).
- **Dev outbox** (default): without SMTP_HOST, messages are logged and
  appended as JSON lines to EMAIL_OUTBOX_DIR/outbox.jsonl (default
  `email_outbox/` under the working directory). Nothing leaves the machine;
  tests and local flows read the token links from the file.

Sending is deliberately best-effort at call sites: account flows must not
500 because the mail provider hiccuped.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_FROM = "Nativo <no-reply@nativo.example>"


def _outbox_path() -> Path:
    root = Path(os.environ.get("EMAIL_OUTBOX_DIR", "email_outbox"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "outbox.jsonl"


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True if handed off successfully."""
    host = os.environ.get("SMTP_HOST")
    if not host:
        record = {
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now(UTC).isoformat(),
        }
        with _outbox_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("Email (dev outbox) to %s: %s", to, subject)
        return True

    message = EmailMessage()
    message["From"] = os.environ.get("EMAIL_FROM", DEFAULT_FROM)
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            if smtp.has_extn("starttls"):
                smtp.starttls()
                smtp.ehlo()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email to %s (%s)", to, subject)
        return False
