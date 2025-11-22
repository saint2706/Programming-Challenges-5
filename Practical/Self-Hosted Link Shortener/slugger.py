"""Utilities for generating and validating slugs for the link shortener."""
from __future__ import annotations

import hashlib
import re
import time
from secrets import token_urlsafe
from typing import Optional

_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")


def _hash_value(value: str, length: int) -> str:
    """Compute a short hash digest for a given string.

    Args:
        value: The input string.
        length: The desired length of the output hash.

    Returns:
        str: Hex digest truncated to `length`.
    """
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=12).hexdigest()
    return digest[:length]


def generate_slug(url: str, attempt: int = 0, length: int = 8) -> str:
    """Generate a deterministic-ish slug from the URL and the attempt counter.

    Uses high-resolution time and random tokens to ensure uniqueness when
    collisions occur (handled by `attempt`).

    Args:
        url: The original URL.
        attempt: Retry counter for collision resolution.
        length: Desired length of the slug.

    Returns:
        str: The generated slug.
    """
    entropy = f"{url}:{time.time_ns()}:{attempt}:{token_urlsafe(4)}"
    return _hash_value(entropy, length)


def validate_custom_slug(slug: str) -> bool:
    """Validate format of a custom slug.

    Allowed: Alphanumeric, underscores, hyphens. Length 4-32.

    Args:
        slug: The slug string to check.

    Returns:
        bool: True if valid, False otherwise.
    """
    return bool(_SLUG_RE.fullmatch(slug))
