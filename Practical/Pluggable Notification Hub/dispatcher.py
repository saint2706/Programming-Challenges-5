"""Dispatcher that fans out messages to configured providers."""

from __future__ import annotations

from typing import Iterable, Sequence

from .providers import NotificationProvider


class NotificationDispatcher:
    """Send messages to all configured providers."""

    def __init__(self, providers: Sequence[NotificationProvider]):
        self.providers = list(providers)

    def notify_all(self, message: str, recipient: str) -> None:
        """Send a message to every configured provider."""

        for provider in self.providers:
            provider.send(message=message, recipient=recipient)

    @classmethod
    def from_providers(cls, providers: Iterable[NotificationProvider]) -> "NotificationDispatcher":
        return cls(list(providers))
