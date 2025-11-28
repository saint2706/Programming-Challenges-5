"""Storage backends for focus intervals."""

from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, date
from typing import Dict, Iterable, List, Optional


class BaseStorage:
    """Shared API for storing focus intervals."""

    def log_interval(self, application: str, start: datetime, end: datetime) -> None:
        """
        Docstring for log_interval.
        """
        duration = (end - start).total_seconds()
        if duration <= 0:
            return
        self._persist_interval(application, start, end, duration)

    def _persist_interval(
        self, application: str, start: datetime, end: datetime, duration: float
    ) -> None:
        """
        Docstring for _persist_interval.
        """
        raise NotImplementedError

    def daily_summary(self, for_date: Optional[date] = None) -> Dict[str, float]:
        """
        Docstring for daily_summary.
        """
        raise NotImplementedError


class SQLiteStorage(BaseStorage):
    """SQLite-backed storage that aggregates per-application durations."""

    def __init__(self, db_path: str = "screen_time.sqlite") -> None:
        """
        Docstring for __init__.
        """
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """
        Docstring for _ensure_tables.
        """
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS focus_intervals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_seconds REAL NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def _persist_interval(
        self, application: str, start: datetime, end: datetime, duration: float
    ) -> None:
        """
        Docstring for _persist_interval.
        """
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                """
                INSERT INTO focus_intervals (application, start_time, end_time, duration_seconds)
                VALUES (?, ?, ?, ?)
                """,
                (
                    application or "Unknown",
                    start.isoformat(),
                    end.isoformat(),
                    duration,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def daily_summary(self, for_date: Optional[date] = None) -> Dict[str, float]:
        """
        Docstring for daily_summary.
        """
        target_date = (for_date or date.today()).isoformat()
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.execute(
                """
                SELECT application, SUM(duration_seconds)
                FROM focus_intervals
                WHERE date(start_time) = ?
                GROUP BY application
                ORDER BY SUM(duration_seconds) DESC
                """,
                (target_date,),
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        finally:
            connection.close()


class JSONStorage(BaseStorage):
    """File-based JSON storage for focus intervals."""

    def __init__(self, file_path: str = "screen_time.json") -> None:
        """
        Docstring for __init__.
        """
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        """
        Docstring for _ensure_file.
        """
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as handle:
                json.dump([], handle)

    def _read_entries(self) -> List[Dict[str, object]]:
        """
        Docstring for _read_entries.
        """
        with open(self.file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_entries(self, entries: Iterable[Dict[str, object]]) -> None:
        """
        Docstring for _write_entries.
        """
        with open(self.file_path, "w", encoding="utf-8") as handle:
            json.dump(list(entries), handle, indent=2)

    def _persist_interval(
        self, application: str, start: datetime, end: datetime, duration: float
    ) -> None:
        """
        Docstring for _persist_interval.
        """
        entries = self._read_entries()
        entries.append(
            {
                "application": application or "Unknown",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration_seconds": duration,
            }
        )
        self._write_entries(entries)

    def daily_summary(self, for_date: Optional[date] = None) -> Dict[str, float]:
        """
        Docstring for daily_summary.
        """
        target_date = (for_date or date.today()).isoformat()
        totals: Dict[str, float] = defaultdict(float)
        for entry in self._read_entries():
            start_time = entry.get("start")
            if not isinstance(start_time, str):
                continue
            if not start_time.startswith(target_date):
                continue
            app_name = str(entry.get("application") or "Unknown")
            totals[app_name] += float(entry.get("duration_seconds") or 0)
        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))
