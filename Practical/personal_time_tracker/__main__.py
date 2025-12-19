"""Command line interface for the personal time tracker."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta
from typing import Iterable

from .logic import TimeTracker


def humanize(duration: timedelta) -> str:
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def render_sessions(rows: Iterable[dict]) -> str:
    lines = [
        "ID        | Category | Start (UTC)          | End (UTC)            | Duration | Notes"
    ]
    lines.append("-" * 90)
    for row in rows:
        duration = humanize(row.get("duration") or row.get("duration", timedelta()))
        lines.append(
            f"{row['id'][:8]} | {row['category']:<8} | {row['start']:<20} | "
            f"{str(row.get('end') or '-'): <20} | {duration} | {row.get('notes', '')}"
        )
    return "\n".join(lines)


def cmd_start(args: argparse.Namespace) -> str:
    tracker = TimeTracker()
    session = tracker.start_session(args.category, notes=args.notes or "")
    return f"Started session {session['id']}"


def cmd_stop(args: argparse.Namespace) -> str:
    tracker = TimeTracker()
    session = tracker.stop_session(notes=args.notes)
    duration = tracker.summarize_sessions([session])[0]["duration"]
    return f"Stopped session {session['id']} after {humanize(duration)}"


def cmd_list(_: argparse.Namespace) -> str:
    tracker = TimeTracker()
    sessions = tracker.summarize_sessions(tracker.list_sessions())
    if not sessions:
        return "No sessions recorded."
    return render_sessions(sessions)


def cmd_report(args: argparse.Namespace) -> str:
    tracker = TimeTracker()
    report = tracker.report(period=args.period)
    if not report:
        return "No completed sessions to report."
    lines = [f"Report ({args.period})"]
    for key, duration in report.items():
        lines.append(f"- {key}: {humanize(duration)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal time tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start a new session")
    start_parser.add_argument(
        "--category", required=True, help="Category of the session"
    )
    start_parser.add_argument("--notes", default="", help="Optional notes")
    start_parser.set_defaults(func=cmd_start)

    stop_parser = subparsers.add_parser("stop", help="Stop the active session")
    stop_parser.add_argument("--notes", default=None, help="Optional notes to append")
    stop_parser.set_defaults(func=cmd_stop)

    list_parser = subparsers.add_parser("list", help="List recorded sessions")
    list_parser.set_defaults(func=cmd_list)

    report_parser = subparsers.add_parser("report", help="Summarize work")
    report_parser.add_argument(
        "--period",
        choices=["daily", "weekly"],
        default="daily",
        help="Aggregation period",
    )
    report_parser.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        message = args.func(args)
    except RuntimeError as exc:  # business rule violation
        parser.error(str(exc))
    print(message)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
