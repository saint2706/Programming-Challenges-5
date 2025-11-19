"""Persistence helpers for the personal time tracker."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_DB_PATH = Path(
    os.environ.get(
        "PTT_DB_PATH",
        Path.home() / ".personal_time_tracker" / "sessions.json",
    )
)


class SessionStore:
    """Simple JSON based storage for time tracking sessions."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else Path(DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> List[Dict]:
        try:
            with self.path.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except json.JSONDecodeError:
            # Corrupt file - keep a backup and reset.
            backup = self.path.with_suffix(".bak")
            self.path.replace(backup)
            self._write([])
            return []

    def _write(self, sessions: List[Dict]) -> None:
        with self.path.open("w", encoding="utf-8") as fp:
            json.dump(sessions, fp, indent=2)

    def all_sessions(self) -> List[Dict]:
        return self._read()

    def save_session(self, session: Dict) -> Dict:
        sessions = self._read()
        sessions.append(session)
        self._write(sessions)
        return session

    def update_session(self, session_id: str, **updates: object) -> Optional[Dict]:
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
        self._write([])
