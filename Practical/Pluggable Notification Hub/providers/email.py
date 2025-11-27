"""Email provider mock implementation."""

from __future__ import annotations

from .base import NotificationProvider


class EmailProvider(NotificationProvider):
    """Send notifications via email."""

    def send(self, message: str, recipient: str) -> None:
        smtp_server = self.options.get("smtp_server", "smtp.example.com")
        sender = self.options.get("sender", "no-reply@example.com")
        print(f"[Email] To: {recipient} | From: {sender} | SMTP: {smtp_server} | Message: {message}")
