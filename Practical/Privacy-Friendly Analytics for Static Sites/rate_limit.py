"""Lightweight rate limiting and bot filtering utilities."""
from __future__ import annotations

import time
from typing import Dict, Tuple

from fastapi import HTTPException, Request


class RateLimiter:
    """In-memory, best-effort rate limiter keyed by IP address."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        """
        Docstring for __init__.
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: Dict[str, Tuple[int, float]] = {}

    def touch(self, key: str) -> None:
        """
        Docstring for touch.
        """
        now = time.time()
        count, window_start = self._hits.get(key, (0, now))

        if now - window_start > self.window_seconds:
            count, window_start = 0, now

        count += 1
        self._hits[key] = (count, window_start)

        if count > self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")


def is_bot_user_agent(user_agent: str | None) -> bool:
    """Return True for obvious bots or crawlers."""
    if not user_agent:
        return False

    lowered = user_agent.lower()
    bot_markers = ("bot", "spider", "crawl", "slurp", "mediapartners-google")
    return any(marker in lowered for marker in bot_markers)


def get_client_ip(request: Request) -> str:
    """
    Docstring for get_client_ip.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "anonymous"
