"""Slack provider mock implementation."""

from __future__ import annotations

from .base import NotificationProvider


class SlackProvider(NotificationProvider):
    """Send notifications to Slack channels or users."""

    def send(self, message: str, recipient: str) -> None:
        """
        Docstring for send.
        """
        webhook_url = self.options.get("webhook_url", "https://hooks.slack.com/services/demo")
        channel = self.options.get("channel", recipient)
        print(f"[Slack] Channel/User: {channel} | Webhook: {webhook_url} | Message: {message}")
