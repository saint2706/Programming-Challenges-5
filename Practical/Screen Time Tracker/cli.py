"""Command line interface for the screen time tracker."""

from __future__ import annotations

import argparse
from datetime import datetime, date
from typing import Optional

from .storage import JSONStorage, SQLiteStorage
from .tracker import build_tracker


def _parse_date(value: Optional[str]) -> Optional[date]:
    """
    Docstring for _parse_date.
    """
    if not value:
        return None
    if value.lower() == "today":
        return date.today()
    return datetime.fromisoformat(value).date()


def start_tracking(args: argparse.Namespace) -> None:
    """
    Docstring for start_tracking.
    """
    tracker = build_tracker(
        backend=args.backend, path=args.path, poll_interval_seconds=args.interval
    )
    tracker.run_forever()


def show_summary(args: argparse.Namespace) -> None:
    """
    Docstring for show_summary.
    """
    target_date = _parse_date(args.date)
    storage = (
        JSONStorage(args.path or "screen_time.json")
        if args.backend == "json"
        else SQLiteStorage(args.path or "screen_time.sqlite")
    )
    summary = storage.daily_summary(target_date)
    print(f"Usage for {target_date or date.today()}:")
    for app, seconds in summary.items():
        hours = seconds / 3600
        print(f"- {app}: {hours:.2f}h")


def build_parser() -> argparse.ArgumentParser:
    """
    Docstring for build_parser.
    """
    parser = argparse.ArgumentParser(description="Track screen time across OSes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    track_parser = subparsers.add_parser("track", help="Start logging focus changes.")
    track_parser.add_argument(
        "--backend", choices=["sqlite", "json"], default="sqlite", help="Storage backend"
    )
    track_parser.add_argument("--path", help="Path to database or JSON file")
    track_parser.add_argument("--interval", type=float, default=5.0, help="Polling interval seconds")
    track_parser.set_defaults(func=start_tracking)

    summary_parser = subparsers.add_parser("summary", help="Show usage summary for a day.")
    summary_parser.add_argument("--backend", choices=["sqlite", "json"], default="sqlite")
    summary_parser.add_argument("--path", help="Path to database or JSON file")
    summary_parser.add_argument(
        "--date",
        default="today",
        help="ISO date (YYYY-MM-DD) or 'today'",
    )
    summary_parser.set_defaults(func=show_summary)
    return parser


def main() -> None:
    """
    Docstring for main.
    """
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
