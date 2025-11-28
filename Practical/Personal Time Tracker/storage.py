"""Persistence helpers for the personal time tracker.

Handles reading and writing session data to a JSON file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

DEFAULT_DB_PATH = Path(
    os.environ.get(
        "PTT_DB_PATH",
        Path.home() / ".personal_time_tracker" / "sessions.json",
    )
)


class SessionStore:
    """Simple JSON based storage for time tracking sessions."""

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the storage.

        Args:
            path: Path to the JSON database file. Defaults to `~/.personal_time_tracker/sessions.json`.
        """
        self.path = Path(path) if path else Path(DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> List[Dict[str, Any]]:
        """Read sessions from the JSON file.

        Returns:
            List[Dict[str, Any]]: List of session records.
        """
        try:
            with self.path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    return data
                # If root is not a list, something is wrong
                return []
        except (json.JSONDecodeError, FileNotFoundError):
            # Corrupt file or missing - keep a backup if corrupt and reset.
            if self.path.exists() and self.path.stat().st_size > 0:
                backup = self.path.with_suffix(".bak")
                self.path.rename(backup)
            self._write([])
            return []

    def _write(self, sessions: List[Dict[str, Any]]) -> None:
        """Write sessions to the JSON file.

        Args:
            sessions: List of session records.
        """
        with self.path.open("w", encoding="utf-8") as fp:
            json.dump(sessions, fp, indent=2)

    def all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve all stored sessions.

        Returns:
            List[Dict[str, Any]]: List of session records.
        """
        return self._read()

    def save_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new session record.

        Args:
            session: The session data to save.

        Returns:
            Dict[str, Any]: The saved session (identity).
        """
        sessions = self._read()
        sessions.append(session)
        self._write(sessions)
        return session

    def update_session(
        self, session_id: str, **updates: Any
    ) -> Optional[Dict[str, Any]]:
        """Update an existing session by ID.

        Args:
            session_id: The UUID of the session.
            **updates: Fields to update.

        Returns:
            Optional[Dict[str, Any]]: The updated session record, or None if not found.
        """
        sessions = self._read()
        target = None
        for entry in sessions:
            if entry.get("id") == session_id:
                entry.update(updates)
                target = entry
                break
        self._write(sessions)
        return target

    def delete_all(self) -> None:
        """Delete all sessions (clear database)."""
        self._write([])
