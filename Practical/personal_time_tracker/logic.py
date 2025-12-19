"""Business logic for the personal time tracker.

This module provides the core API for managing time tracking sessions, including
starting, stopping, listing, and summarizing work intervals.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from .storage import SessionStore


def utcnow() -> datetime:
    """Get the current time in UTC.

    Returns:
        datetime: Current UTC datetime.
    """
    return datetime.now(timezone.utc)


class TimeTracker:
    """High level API for recording work sessions.

    Attributes:
        store: The persistence layer for session data.
        _now: Function to get current time (dependency injection for testing).
    """

    def __init__(
        self,
        store: Optional[SessionStore] = None,
        now_func: Callable[[], datetime] = utcnow,
    ) -> None:
        """Initialize the TimeTracker.

        Args:
            store: Custom SessionStore instance.
            now_func: Function returning current datetime.
        """
        self.store = store or SessionStore()
        self._now = now_func

    def start_session(self, category: str, notes: str = "") -> Dict[str, Any]:
        """Start a new work session.

        Args:
            category: The category of work (e.g., "coding", "meeting").
            notes: Optional notes describing the session.

        Returns:
            Dict[str, Any]: The created session record.

        Raises:
            RuntimeError: If there is already an active (unfinished) session.
        """
        active = self.get_active_session()
        if active:
            raise RuntimeError(
                "There is already an active session. Stop it before starting a new one."
            )
        session = {
            "id": uuid.uuid4().hex,
            "category": category,
            "notes": notes,
            "start": self._now().isoformat(),
            "end": None,
        }
        return self.store.save_session(session)

    def stop_session(self, notes: Optional[str] = None) -> Dict[str, Any]:
        """Stop the currently active session.

        Args:
            notes: Additional notes to append to the session.

        Returns:
            Dict[str, Any]: The updated session record.

        Raises:
            RuntimeError: If there is no active session to stop.
        """
        active = self.get_active_session()
        if not active:
            raise RuntimeError("No active session to stop.")
        updates = {"end": self._now().isoformat()}
        if notes:
            # Append notes if they exist
            current_notes = active.get("notes") or ""
            updates["notes"] = (current_notes + f" {notes}".rstrip()).strip()

        # We know active['id'] exists because it came from store
        result = self.store.update_session(active["id"], **updates)
        if result is None:
            # Should typically not happen if active was just fetched
            raise RuntimeError("Failed to update session.")
        return result

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all recorded sessions, sorted by start time.

        Returns:
            List[Dict[str, Any]]: List of session records.
        """
        sessions = self.store.all_sessions()
        sessions.sort(key=lambda item: item.get("start", ""))
        return sessions

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active session, if any.

        Returns:
            Optional[Dict[str, Any]]: The active session record or None.
        """
        sessions = self.store.all_sessions()
        # Search from newest to oldest for an open session
        for entry in reversed(sessions):
            if entry.get("end") is None:
                return entry
        return None

    @staticmethod
    def _duration(session: Dict[str, Any]) -> timedelta:
        """Calculate duration of a finished session."""
        if not session.get("end"):
            return timedelta(0)
        start = datetime.fromisoformat(session["start"])
        end = datetime.fromisoformat(session["end"])
        return end - start

    def report(self, period: str = "daily") -> Dict[str, timedelta]:
        """Generate a duration report grouped by time period.

        Args:
            period: Grouping granularity ("daily" or "weekly").

        Returns:
            Dict[str, timedelta]: Mapping of period label to total duration.
        """
        sessions = [s for s in self.store.all_sessions() if s.get("end")]
        buckets: Dict[str, timedelta] = defaultdict(timedelta)
        for session in sessions:
            # Parse start time
            # Note: This assumes ISO format strings are valid
            start = datetime.fromisoformat(session["start"])
            if start.tzinfo is None:
                # Assume UTC if naive, though typically we store ISO with TZ or UTC
                start = start.replace(tzinfo=timezone.utc)
            else:
                start = start.astimezone(timezone.utc)

            duration = self._duration(session)

            if period == "weekly":
                year, week, _ = start.isocalendar()
                key = f"{year}-W{week:02d}"
            else:
                key = start.date().isoformat()
            buckets[key] += duration
        return dict(sorted(buckets.items()))

    def summarize_sessions(
        self, sessions: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add calculated duration to a list of sessions.

        Args:
            sessions: Iterable of session records.

        Returns:
            List[Dict[str, Any]]: Sessions with an added "duration" field.
        """
        summary = []
        for session in sessions:
            duration = self._duration(session)
            summary.append({**session, "duration": duration})
        return summary
