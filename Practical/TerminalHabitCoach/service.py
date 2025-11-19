"""High-level habit tracking services."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional

from .database import HabitRepository, Habit


@dataclass
class Reminder:
    habit: Habit
    reminder_time: str

    def render(self) -> str:
        return f"⏰ {self.habit.name} at {self.reminder_time}"


class TerminalHabitCoach:
    """Coordinates data access with business rules and presentation helpers."""

    def __init__(self, repository: Optional[HabitRepository] = None) -> None:
        self.repo = repository or HabitRepository()

    # Habit management -------------------------------------------------
    def add_habit(
        self,
        name: str,
        description: str = "",
        frequency: str = "daily",
        reminder_time: Optional[str] = None,
    ) -> Habit:
        return self.repo.add_habit(name, description, frequency, reminder_time)

    def list_status(self) -> List[str]:
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
        stats = self.repo.get_all_stats()
        lines: List[str] = []
        if not stats:
            return ["No streaks to display. Log some habits!"]
        for stat in stats:
            habit = stat["habit"]
            current = stat["current_streak"]
            longest = stat["longest_streak"]
            days_since = stat["days_since_log"]
            freshness = "today" if days_since == 0 else f"{days_since} day(s) ago" if days_since is not None else "never"
            lines.append(
                f"🔥 {habit.name}: current {current} days, longest {longest} days, last logged {freshness}."
            )
        return lines

    def render_reminders(self) -> List[str]:
        reminders = [Reminder(habit=h, reminder_time=h.reminder_time) for h in self.repo.habits_needing_reminder()]
        return [reminder.render() for reminder in reminders]

    def log(self, habit_name: str, when: Optional[str] = None, note: Optional[str] = None) -> None:
        when_dt = datetime.fromisoformat(when) if when else None
        self.repo.log_habit(habit_name, when=when_dt, note=note)

    def habit_summary(self, habit_name: str) -> List[str]:
        stat = self.repo.get_habit_stats(habit_name)
        habit = stat["habit"]
        lines = [f"Habit: {habit.name}", f"Description: {habit.description or '—'}"]
        lines.append(f"Frequency: {habit.frequency}")
        lines.append(f"Reminder: {habit.reminder_time or '—'}")
        lines.append(f"Total logs: {stat['total_logs']}")
        lines.append(f"Current streak: {stat['current_streak']} (longest {stat['longest_streak']})")
        last = stat["last_logged"] or "never"
        lines.append(f"Last logged: {last}")
        recent = self.repo.recent_logs(habit_name)
        if recent:
            lines.append("Recent entries:")
            for entry in recent:
                lines.append(f"  • {entry}")
        return lines
