"""Business logic for the personal time tracker."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from .storage import SessionStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimeTracker:
    """High level API for recording work sessions."""

    def __init__(self, store: Optional[SessionStore] = None, now_func=utcnow) -> None:
        self.store = store or SessionStore()
        self._now = now_func

    def start_session(self, category: str, notes: str = "") -> Dict:
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

    def stop_session(self, notes: Optional[str] = None) -> Dict:
        active = self.get_active_session()
        if not active:
            raise RuntimeError("No active session to stop.")
        updates = {"end": self._now().isoformat()}
        if notes:
            updates["notes"] = (active.get("notes") or "") + f" {notes}".rstrip()
        return self.store.update_session(active["id"], **updates)  # type: ignore[return-value]

    def list_sessions(self) -> List[Dict]:
        sessions = self.store.all_sessions()
        sessions.sort(key=lambda item: item.get("start", ""))
        return sessions

    def get_active_session(self) -> Optional[Dict]:
        sessions = self.store.all_sessions()
        for entry in reversed(sessions):
            if entry.get("end") is None:
                return entry
        return None

    @staticmethod
    def _duration(session: Dict) -> timedelta:
        if not session.get("end"):
            return timedelta(0)
        start = datetime.fromisoformat(session["start"])
        end = datetime.fromisoformat(session["end"])
        return end - start

    def report(self, period: str = "daily") -> Dict[str, timedelta]:
        sessions = [s for s in self.store.all_sessions() if s.get("end")]
        buckets: Dict[str, timedelta] = defaultdict(timedelta)
        for session in sessions:
            start = datetime.fromisoformat(session["start"]).astimezone(timezone.utc)
            duration = self._duration(session)
            if period == "weekly":
                year, week, _ = start.isocalendar()
                key = f"{year}-W{week:02d}"
            else:
                key = start.date().isoformat()
            buckets[key] += duration
        return dict(sorted(buckets.items()))

    def summarize_sessions(self, sessions: Iterable[Dict]) -> List[Dict]:
        summary = []
        for session in sessions:
            duration = self._duration(session)
            summary.append({**session, "duration": duration})
        return summary
