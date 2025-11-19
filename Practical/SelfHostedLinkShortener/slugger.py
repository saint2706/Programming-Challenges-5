"""Utilities for generating and validating slugs for the link shortener."""
from __future__ import annotations

import hashlib
import re
import time
from secrets import token_urlsafe

_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")


def _hash_value(value: str, length: int) -> str:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=12).hexdigest()
    return digest[:length]


def generate_slug(url: str, attempt: int = 0, length: int = 8) -> str:
    """Generate a deterministic-ish slug from the URL and the attempt counter."""

    entropy = f"{url}:{time.time_ns()}:{attempt}:{token_urlsafe(4)}"
    return _hash_value(entropy, length)


def validate_custom_slug(slug: str) -> bool:
    return bool(_SLUG_RE.fullmatch(slug))
