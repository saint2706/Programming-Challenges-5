"""SQLite data-access layer for the Terminal Habit Coach.

Handles database connections, schema migrations, and CRUD operations for habits.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import sqlite3
from typing import Iterable, List, Optional, Sequence, Union, Any, Dict

DEFAULT_DB_PATH = Path.home() / ".terminal_habit_coach.db"


@dataclass
class Habit:
    """Representation of a habit record.

    Attributes:
        id: Database ID.
        name: Unique name.
        description: Short description.
        frequency: Tracking cadence.
        reminder_time: Optional HH:MM string.
    """

    id: int
    name: str
    description: str
    frequency: str
    reminder_time: Optional[str]


class HabitRepository:
    """Data-access layer that encapsulates SQLite operations."""

    def __init__(self, db_path: Optional[Union[Path, str]] = None) -> None:
        """Initialize the repository.

        Args:
            db_path: Path to the SQLite file. Defaults to ~/.terminal_habit_coach.db.
        """
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a configured database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    frequency TEXT DEFAULT 'daily',
                    reminder_time TEXT
                );

                CREATE TABLE IF NOT EXISTS log_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                    logged_at TEXT NOT NULL,
                    note TEXT
                );

                CREATE TABLE IF NOT EXISTS streak_metadata (
                    habit_id INTEGER PRIMARY KEY REFERENCES habits(id) ON DELETE CASCADE,
                    last_logged_date TEXT,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0
                );
                """
            )

    # ------------------------------------------------------------------
    # Habit CRUD operations
    # ------------------------------------------------------------------
    def add_habit(
        self,
        name: str,
        description: str = "",
        frequency: str = "daily",
        reminder_time: Optional[str] = None,
    ) -> Habit:
        """Create a new habit.

        Args:
            name: Habit name.
            description: Description.
            frequency: Frequency.
            reminder_time: Reminder time string.

        Returns:
            Habit: The created habit.
        """
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO habits(name, description, frequency, reminder_time) VALUES (?, ?, ?, ?)",
                (name.strip(), description.strip(), frequency, reminder_time),
            )
            habit_id = cur.lastrowid
            conn.execute(
                "INSERT OR IGNORE INTO streak_metadata(habit_id, current_streak, longest_streak) VALUES (?, 0, 0)",
                (habit_id,),
            )
        return self.get_habit_by_name(name)

    def get_habit_by_name(self, name: str) -> Habit:
        """Retrieve a habit by name.

        Args:
            name: The habit name.

        Returns:
            Habit: The habit object.

        Raises:
            ValueError: If habit not found.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM habits WHERE name = ?", (name.strip(),)
            ).fetchone()
        if not row:
            raise ValueError(f"Habit '{name}' not found")
        return Habit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            frequency=row["frequency"],
            reminder_time=row["reminder_time"],
        )

    def list_habits(self) -> List[Habit]:
        """List all habits ordered by name.

        Returns:
            List[Habit]: List of habits.
        """
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM habits ORDER BY name").fetchall()
        return [
            Habit(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                frequency=row["frequency"],
                reminder_time=row["reminder_time"],
            )
            for row in rows
        ]

    def delete_habit(self, name: str) -> None:
        """Delete a habit by name.

        Args:
            name: Habit name.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM habits WHERE name = ?", (name.strip(),))

    # ------------------------------------------------------------------
    # Logging operations
    # ------------------------------------------------------------------
    def log_habit(
        self,
        name: str,
        when: Optional[datetime] = None,
        note: Optional[str] = None,
    ) -> None:
        """Log an occurrence of a habit.

        Args:
            name: Habit name.
            when: Datetime of the log (default now).
            note: Optional note.
        """
        habit = self.get_habit_by_name(name)
        when = when or datetime.now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO log_entries(habit_id, logged_at, note) VALUES (?, ?, ?)",
                (habit.id, when.isoformat(), note),
            )
        self._update_streaks(habit.id, when.date())

    def _update_streaks(self, habit_id: int, log_date: date) -> None:
        """Recalculate streaks after a log entry."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_logged_date, current_streak, longest_streak FROM streak_metadata WHERE habit_id = ?",
                (habit_id,),
            ).fetchone()

            if not row:
                # Should exist if created with add_habit, but handle edge case
                conn.execute(
                    "INSERT INTO streak_metadata(habit_id, last_logged_date, current_streak, longest_streak) VALUES (?, ?, 1, 1)",
                    (habit_id, log_date.isoformat()),
                )
                return

            last_logged = row["last_logged_date"]
            current_streak = row["current_streak"]
            longest_streak = row["longest_streak"]

            if last_logged:
                last_date = datetime.fromisoformat(last_logged).date()
                delta = (log_date - last_date).days
                if delta == 0:
                    # already logged today; do not double count streak
                    return
                if delta == 1:
                    # consecutive day
                    current_streak += 1
                else:
                    # broken streak (assuming future dates not allowed or handled elsewhere)
                    current_streak = 1
            else:
                # first log
                current_streak = 1

            longest_streak = max(longest_streak, current_streak)

            conn.execute(
                "UPDATE streak_metadata SET last_logged_date = ?, current_streak = ?, longest_streak = ? WHERE habit_id = ?",
                (log_date.isoformat(), current_streak, longest_streak, habit_id),
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_habit_stats(self, habit_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a habit.

        Args:
            habit_name: Habit name.

        Returns:
            dict: Stats including streaks and counts.
        """
        habit = self.get_habit_by_name(habit_name)
        with self._connect() as conn:
            log_row = conn.execute(
                "SELECT COUNT(*) AS total, MAX(logged_at) AS last_logged FROM log_entries WHERE habit_id = ?",
                (habit.id,),
            ).fetchone()
            streak_row = conn.execute(
                "SELECT last_logged_date, current_streak, longest_streak FROM streak_metadata WHERE habit_id = ?",
                (habit.id,),
            ).fetchone()

        last_logged_date_str = (
            streak_row["last_logged_date"] if streak_row else None
        )
        if last_logged_date_str:
            last_logged_date = datetime.fromisoformat(last_logged_date_str).date()
            days_since = (date.today() - last_logged_date).days
        else:
            days_since = None

        return {
            "habit": habit,
            "total_logs": log_row["total"] if log_row else 0,
            "last_logged": log_row["last_logged"],
            "current_streak": streak_row["current_streak"] if streak_row else 0,
            "longest_streak": streak_row["longest_streak"] if streak_row else 0,
            "days_since_log": days_since,
        }

    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get stats for all habits."""
        return [self.get_habit_stats(habit.name) for habit in self.list_habits()]

    def habits_needing_reminder(self, on_date: Optional[date] = None) -> List[Habit]:
        """Find habits with a reminder set that haven't been logged on the given date.

        Args:
            on_date: The reference date (default today).

        Returns:
            List[Habit]: Habits needing attention.
        """
        on_date = on_date or date.today()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT h.* FROM habits h
                LEFT JOIN streak_metadata s ON h.id = s.habit_id
                WHERE h.reminder_time IS NOT NULL
                AND (s.last_logged_date IS NULL OR DATE(s.last_logged_date) <> ?)
                ORDER BY h.name
                """,
                (on_date.isoformat(),),
            ).fetchall()
        return [
            Habit(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                frequency=row["frequency"],
                reminder_time=row["reminder_time"],
            )
            for row in rows
        ]

    def recent_logs(self, habit_name: str, limit: int = 5) -> Sequence[str]:
        """Get recent log timestamps for a habit.

        Args:
            habit_name: Habit name.
            limit: Max entries.

        Returns:
            Sequence[str]: List of timestamp strings.
        """
        habit = self.get_habit_by_name(habit_name)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT logged_at FROM log_entries WHERE habit_id = ? ORDER BY logged_at DESC LIMIT ?",
                (habit.id, limit),
            ).fetchall()
        return [row["logged_at"] for row in rows]
