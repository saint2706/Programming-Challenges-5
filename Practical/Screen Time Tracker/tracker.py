"""Main tracker logic for scheduling and recording focus changes."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Optional

from .os_interfaces import ActiveWindowProvider, WindowInfo, get_provider_for_platform
from .storage import BaseStorage, JSONStorage, SQLiteStorage


class ScreenTimeTracker:
    """Track focus changes and persist them on interval switches."""

    def __init__(
        self,
        provider: Optional[ActiveWindowProvider] = None,
        storage: Optional[BaseStorage] = None,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        """
        Docstring for __init__.
        """
        self.provider = provider or get_provider_for_platform()
        self.storage = storage or SQLiteStorage()
        self.poll_interval_seconds = poll_interval_seconds
        self._last_window: Optional[WindowInfo] = None
        self._last_switch: Optional[datetime] = None
        self._stop_event = threading.Event()

    def _now(self) -> datetime:
        """
        Docstring for _now.
        """
        return datetime.now(timezone.utc)

    def _record_interval(self, current_time: datetime) -> None:
        """
        Docstring for _record_interval.
        """
        if not self._last_window or not self._last_switch:
            return
        self.storage.log_interval(self._last_window.title, self._last_switch, current_time)

    def poll(self) -> None:
        """Capture focus changes and persist the elapsed time."""

        active_window = self.provider.get_active_window()
        now = self._now()
        if active_window and self._last_window and active_window.title == self._last_window.title:
            return
        if self._last_window:
            self._record_interval(now)
        self._last_window = active_window
        self._last_switch = now

    def run_forever(self) -> None:
        """Start the scheduler loop until stop() is invoked or interrupted."""

        self._stop_event.clear()
        try:
            while not self._stop_event.is_set():
                self.poll()
                time.sleep(self.poll_interval_seconds)
        except KeyboardInterrupt:
            self.stop()
        finally:
            self._record_interval(self._now())

    def run_in_thread(self) -> threading.Thread:
        """
        Docstring for run_in_thread.
        """
        thread = threading.Thread(target=self.run_forever, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """
        Docstring for stop.
        """
        self._stop_event.set()


def build_tracker(
    backend: str = "sqlite",
    path: Optional[str] = None,
    poll_interval_seconds: float = 5.0,
) -> ScreenTimeTracker:
    """Helper to construct a tracker from CLI/GUI inputs."""

    storage: BaseStorage
    if backend == "json":
        storage = JSONStorage(path or "screen_time.json")
    else:
        storage = SQLiteStorage(path or "screen_time.sqlite")
    return ScreenTimeTracker(storage=storage, poll_interval_seconds=poll_interval_seconds)
