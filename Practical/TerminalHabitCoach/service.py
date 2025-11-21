"""High-level habit tracking services.

Orchestrates the business logic for managing habits, tracking streaks, and
generating reminders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional, Any

from .database import HabitRepository, Habit


@dataclass
class Reminder:
    """A habit reminder tuple.

    Attributes:
        habit: The habit needing attention.
        reminder_time: The scheduled time for the reminder.
    """

    habit: Habit
    reminder_time: str

    def render(self) -> str:
        """Format the reminder for display."""
        return f"⏰ {self.habit.name} at {self.reminder_time}"


class TerminalHabitCoach:
    """Coordinates data access with business rules and presentation helpers."""

    def __init__(self, repository: Optional[HabitRepository] = None) -> None:
        """Initialize the coach service.

        Args:
            repository: Data persistence layer.
        """
        self.repo = repository or HabitRepository()

    # Habit management -------------------------------------------------
    def add_habit(
        self,
        name: str,
        description: str = "",
        frequency: str = "daily",
        reminder_time: Optional[str] = None,
    ) -> Habit:
        """Register a new habit.

        Args:
            name: Unique name of the habit.
            description: Optional description.
            frequency: Tracking frequency (e.g., "daily").
            reminder_time: Optional HH:MM time for reminders.

        Returns:
            Habit: The created habit.
        """
        return self.repo.add_habit(name, description, frequency, reminder_time)

    def list_status(self) -> List[str]:
        """Generate a status report table of all habits.

        Returns:
            List[str]: Lines of text representing the status table.
        """
        lines: List[str] = []
        stats = self.repo.get_all_stats()
        if not stats:
            return ["No habits yet. Add one with 'add-habit'."]
        header = f"{'Habit':20} {'Streak':>8} {'Longest':>8} {'Total':>6} {'Last Logged':>20}"
        lines.append(header)
        lines.append("-" * len(header))
        for stat in stats:
            habit = stat["habit"]
            last_logged = stat["last_logged"] or "—"
            lines.append(
                f"{habit.name:20} {stat['current_streak']:>8} {stat['longest_streak']:>8} {stat['total_logs']:>6} {last_logged:>20}"
            )
        reminders = self.render_reminders()
        if reminders:
            lines.append("")
            lines.append("Reminders:")
            lines.extend(reminders)
        return lines

    def render_streaks(self) -> List[str]:
        """Generate detailed streak information.

        Returns:
            List[str]: Lines of text describing streaks.
        """
        stats = self.repo.get_all_stats()
        lines: List[str] = []
        if not stats:
            return ["No streaks to display. Log some habits!"]
        for stat in stats:
            habit = stat["habit"]
            current = stat["current_streak"]
            longest = stat["longest_streak"]
            days_since = stat["days_since_log"]

            freshness = "never"
            if days_since == 0:
                freshness = "today"
            elif days_since is not None:
                freshness = f"{days_since} day(s) ago"

            lines.append(
                f"🔥 {habit.name}: current {current} days, longest {longest} days, last logged {freshness}."
            )
        return lines

    def render_reminders(self) -> List[str]:
        """Generate reminders for habits due today.

        Returns:
            List[str]: Formatted reminder strings.
        """
        reminders = [
            Reminder(habit=h, reminder_time=h.reminder_time)  # type: ignore
            for h in self.repo.habits_needing_reminder()
            if h.reminder_time
        ]
        return [reminder.render() for reminder in reminders]

    def log(
        self,
        habit_name: str,
        when: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        """Log a completion for a habit.

        Args:
            habit_name: The name of the habit.
            when: ISO timestamp string (defaults to now).
            note: Optional journal note.
        """
        when_dt = datetime.fromisoformat(when) if when else None
        self.repo.log_habit(habit_name, when=when_dt, note=note)

    def habit_summary(self, habit_name: str) -> List[str]:
        """Generate a summary view for a single habit.

        Args:
            habit_name: Name of the habit.

        Returns:
            List[str]: Lines of summary text.
        """
        stat = self.repo.get_habit_stats(habit_name)
        habit = stat["habit"]
        lines = [
            f"Habit: {habit.name}",
            f"Description: {habit.description or '—'}",
        ]
        lines.append(f"Frequency: {habit.frequency}")
        lines.append(f"Reminder: {habit.reminder_time or '—'}")
        lines.append(f"Total logs: {stat['total_logs']}")
        lines.append(
            f"Current streak: {stat['current_streak']} (longest {stat['longest_streak']})"
        )
        last = stat["last_logged"] or "never"
        lines.append(f"Last logged: {last}")
        recent = self.repo.recent_logs(habit_name)
        if recent:
            lines.append("Recent entries:")
            for entry in recent:
                lines.append(f"  • {entry}")
        return lines
