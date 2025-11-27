"""SMS provider mock implementation."""

from __future__ import annotations

from .base import NotificationProvider


class SMSProvider(NotificationProvider):
    """Send notifications via SMS."""

    def send(self, message: str, recipient: str) -> None:
        gateway = self.options.get("gateway", "twilio")
        sender_id = self.options.get("sender_id", "NotifyBot")
        print(f"[SMS] To: {recipient} | Sender: {sender_id} | Gateway: {gateway} | Message: {message}")
