"""SQLite persistence helpers for the self-hosted link shortener."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

_DB_FILENAME = "shortener.db"


def _get_db_path() -> Path:
    """Return the path to the SQLite database file.

    The path can be overridden by setting the ``SHORTENER_DB_PATH`` environment
    variable. This is especially helpful for tests that need an isolated
    database instance.

    Returns:
        Path: Path object to the database file.
    """

    override = os.environ.get("SHORTENER_DB_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / _DB_FILENAME


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with sensible defaults.

    Yields:
        sqlite3.Connection: Active database connection.
    """

    path = _get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def initialize_db() -> None:
    """Create the ``links`` table if it does not already exist."""

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                slug TEXT PRIMARY KEY,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT,
                hit_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def create_link(slug: str, url: str) -> Dict[str, Any]:
    """Insert a new short link record.

    Args:
        slug: The unique short slug.
        url: The destination URL.

    Returns:
        Dict[str, Any]: The created record dict.
    """

    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO links (slug, original_url, created_at, hit_count) VALUES (?, ?, ?, 0)",
            (slug, url, now),
        )
        conn.commit()
    return {"slug": slug, "original_url": url, "created_at": now, "hit_count": 0}


def get_link(slug: str) -> Optional[Dict[str, Any]]:
    """Fetch a single link record by slug.

    Args:
        slug: The slug to look up.

    Returns:
        Optional[Dict[str, Any]]: The link record or None.
    """

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM links WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    return dict(row)


def list_links(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return all known links sorted by creation date.

    Args:
        limit: Max number of links to return.

    Returns:
        List[Dict[str, Any]]: List of link records.
    """

    query = "SELECT * FROM links ORDER BY datetime(created_at) DESC"
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def delete_link(slug: str) -> bool:
    """Delete a link by slug.

    Args:
        slug: The slug to delete.

    Returns:
        bool: ``True`` if a row was removed, ``False`` otherwise.
    """

    with get_connection() as conn:
        cur = conn.execute("DELETE FROM links WHERE slug = ?", (slug,))
        conn.commit()
    return cur.rowcount > 0


def increment_hit(slug: str) -> None:
    """Increment the hit counter and update ``last_accessed_at``.

    Args:
        slug: The slug to update.
    """

    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE links
            SET hit_count = hit_count + 1,
                last_accessed_at = ?
            WHERE slug = ?
            """,
            (now, slug),
        )
        conn.commit()


def slug_exists(slug: str) -> bool:
    """Check if a slug is already in use.

    Args:
        slug: The slug to check.

    Returns:
        bool: True if exists.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM links WHERE slug = ?", (slug,)).fetchone()
    return row is not None
