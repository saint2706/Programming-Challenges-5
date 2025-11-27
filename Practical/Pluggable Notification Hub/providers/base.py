"""Base class for notification providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class NotificationProvider(ABC):
    """Abstract notification provider interface."""

    name: str

    def __init__(self, **options: Any) -> None:
        self.options: Dict[str, Any] = options
        self.name = self.__class__.__name__.replace("Provider", "")

    @abstractmethod
    def send(self, message: str, recipient: str) -> None:
        """Send the message to the recipient."""
        raise NotImplementedError

    def describe(self) -> str:
        """Return a human-readable description for debugging/logging."""
        return f"{self.name} provider (options={self.options})"
