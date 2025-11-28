"""CLI for the Terminal Habit Coach."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

# Hack to support running as a script despite spaces in folder name
sys.path.append(os.path.dirname(__file__))

try:
    from database import HabitRepository
    from service import TerminalHabitCoach
except ImportError:
    from .database import HabitRepository
    from .service import TerminalHabitCoach


def build_parser() -> argparse.ArgumentParser:
    """Construct the command line parser."""
    parser = argparse.ArgumentParser(description="Terminal Habit Coach", prog="thc")
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Optional path to the SQLite database file (defaults to ~/.terminal_habit_coach.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_habit = subparsers.add_parser("add-habit", help="Register a new habit")
    add_habit.add_argument("name", help="Habit name")
    add_habit.add_argument(
        "--description", default="", help="Description for the habit"
    )
    add_habit.add_argument(
        "--frequency", default="daily", help="Tracking frequency label"
    )
    add_habit.add_argument(
        "--reminder",
        dest="reminder",
        help="Optional reminder time (HH:MM)",
    )

    log_cmd = subparsers.add_parser("log", help="Log progress for a habit")
    log_cmd.add_argument("name", help="Habit name")
    log_cmd.add_argument("--when", help="ISO timestamp to log (defaults to now)")
    log_cmd.add_argument("--note", help="Optional note")

    subparsers.add_parser("status", help="Display summary table")

    subparsers.add_parser("streaks", help="Display streak details")

    show_cmd = subparsers.add_parser("show", help="Display details for a single habit")
    show_cmd.add_argument("name", help="Habit name")

    return parser


def _build_coach(db_path: Optional[Path]) -> TerminalHabitCoach:
    """Factory for the coach service."""
    repo = HabitRepository(db_path=db_path) if db_path else HabitRepository()
    return TerminalHabitCoach(repository=repo)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Command line arguments.

    Returns:
        int: Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    coach = _build_coach(args.database)

    if args.command == "add-habit":
        coach.add_habit(args.name, args.description, args.frequency, args.reminder)
        print(f"Added habit '{args.name}'.")
        return 0
    if args.command == "log":
        coach.log(args.name, when=args.when, note=args.note)
        print(f"Logged progress for '{args.name}'.")
        return 0
    if args.command == "status":
        for line in coach.list_status():
            print(line)
        return 0
    if args.command == "streaks":
        for line in coach.render_streaks():
            print(line)
        return 0
    if args.command == "show":
        try:
            for line in coach.habit_summary(args.name):
                print(line)
        except ValueError as e:
            print(f"Error: {e}")
            return 1
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
