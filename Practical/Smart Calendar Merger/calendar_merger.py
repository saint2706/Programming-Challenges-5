#!/usr/bin/env python3
"""
Smart Calendar Merger

A CLI tool for parsing, merging, and analyzing iCalendar (.ics) files.
Supports merging multiple calendars, detecting scheduling conflicts,
and filtering events by date range or search query.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator

import pytz
from dateutil import rrule
from dateutil.parser import parse as parse_date
from icalendar import Calendar
from icalendar import Event as ICalEvent


@dataclass
class Event:
    """Represents a calendar event with normalized fields."""

    uid: str
    summary: str
    start: datetime
    end: datetime
    description: str = ""
    location: str = ""
    all_day: bool = False
    source_file: str = ""
    recurrence_id: str | None = None

    def overlaps(self, other: Event) -> bool:
        """Check if this event overlaps with another event."""
        # All-day events don't conflict with timed events
        if self.all_day != other.all_day:
            return False
        return self.start < other.end and other.start < self.end

    def to_dict(self) -> dict:
        """Convert event to dictionary for JSON serialization."""
        return {
            "uid": self.uid,
            "summary": self.summary,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "location": self.location,
            "all_day": self.all_day,
            "source_file": self.source_file,
        }

    def to_ical_event(self) -> ICalEvent:
        """Convert to an iCalendar Event component."""
        event = ICalEvent()
        event.add("uid", self.uid)
        event.add("summary", self.summary)
        event.add("description", self.description)
        event.add("location", self.location)

        if self.all_day:
            event.add("dtstart", self.start.date())
            event.add("dtend", self.end.date())
        else:
            event.add("dtstart", self.start)
            event.add("dtend", self.end)

        return event


@dataclass
class Conflict:
    """Represents a scheduling conflict between two events."""

    event1: Event
    event2: Event
    overlap_start: datetime = field(init=False)
    overlap_end: datetime = field(init=False)

    def __post_init__(self) -> None:
        self.overlap_start = max(self.event1.start, self.event2.start)
        self.overlap_end = min(self.event1.end, self.event2.end)

    @property
    def overlap_duration(self) -> timedelta:
        """Duration of the overlap."""
        return self.overlap_end - self.overlap_start

    def to_dict(self) -> dict:
        """Convert conflict to dictionary for JSON serialization."""
        return {
            "event1": self.event1.to_dict(),
            "event2": self.event2.to_dict(),
            "overlap_start": self.overlap_start.isoformat(),
            "overlap_end": self.overlap_end.isoformat(),
            "overlap_duration_minutes": self.overlap_duration.total_seconds() / 60,
        }


def normalize_datetime(
    dt: datetime | date, timezone: pytz.BaseTzInfo | None = None
) -> datetime:
    """
    Normalize a date or datetime to a timezone-aware datetime.

    Args:
        dt: Date or datetime to normalize
        timezone: Target timezone (defaults to UTC)

    Returns:
        Timezone-aware datetime
    """
    if timezone is None:
        timezone = pytz.UTC

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return timezone.localize(dt)
        return dt.astimezone(timezone)
    else:
        # It's a date, convert to datetime at midnight
        return timezone.localize(datetime.combine(dt, datetime.min.time()))


def parse_ical_file(filepath: Path) -> Iterator[Event]:
    """
    Parse an iCalendar file and yield Event objects.

    Args:
        filepath: Path to the .ics file

    Yields:
        Event objects parsed from the calendar
    """
    with open(filepath, "rb") as f:
        cal = Calendar.from_ical(f.read())

    for component in cal.walk():
        if component.name == "VEVENT":
            yield _parse_vevent(component, str(filepath))


def _parse_vevent(component: ICalEvent, source_file: str) -> Event:
    """Parse a VEVENT component into an Event object."""
    uid = str(component.get("uid", ""))
    summary = str(component.get("summary", "No Title"))
    description = str(component.get("description", ""))
    location = str(component.get("location", ""))

    dtstart = component.get("dtstart")
    dtend = component.get("dtend")

    # Determine if this is an all-day event
    all_day = False
    if dtstart:
        all_day = not isinstance(dtstart.dt, datetime)

    # Normalize start/end times
    start = normalize_datetime(dtstart.dt) if dtstart else datetime.now(pytz.UTC)

    if dtend:
        end = normalize_datetime(dtend.dt)
    elif all_day:
        # All-day events without end default to 1 day
        end = start + timedelta(days=1)
    else:
        # Timed events without end default to 1 hour
        end = start + timedelta(hours=1)

    return Event(
        uid=uid,
        summary=summary,
        start=start,
        end=end,
        description=description,
        location=location,
        all_day=all_day,
        source_file=source_file,
    )


def expand_recurring_events(
    events: list[Event],
    start_range: datetime,
    end_range: datetime,
    cal_path: Path,
) -> list[Event]:
    """
    Expand recurring events within a date range.

    Args:
        events: List of base events
        start_range: Start of the range to expand
        end_range: End of the range to expand
        cal_path: Path to the calendar file for re-parsing RRULE

    Returns:
        List of events including expanded recurrences
    """
    expanded: list[Event] = []

    # Re-read the calendar to access RRULE data
    with open(cal_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    event_map = {e.uid: e for e in events}

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("uid", ""))
        rrule_prop = component.get("rrule")

        if uid not in event_map:
            continue

        base_event = event_map[uid]

        if rrule_prop:
            # Parse and expand the recurrence rule
            rule_str = rrule_prop.to_ical().decode("utf-8")
            duration = base_event.end - base_event.start

            try:
                rule = rrule.rrulestr(
                    f"RRULE:{rule_str}",
                    dtstart=base_event.start,
                )
                occurrences = list(rule.between(start_range, end_range, inc=True))

                for i, occ_start in enumerate(occurrences):
                    expanded.append(
                        Event(
                            uid=f"{uid}_occ_{i}",
                            summary=base_event.summary,
                            start=occ_start,
                            end=occ_start + duration,
                            description=base_event.description,
                            location=base_event.location,
                            all_day=base_event.all_day,
                            source_file=base_event.source_file,
                            recurrence_id=uid,
                        )
                    )
            except (ValueError, TypeError):
                # If RRULE parsing fails, include the base event
                if start_range <= base_event.start <= end_range:
                    expanded.append(base_event)
        else:
            # Non-recurring event
            if start_range <= base_event.start <= end_range:
                expanded.append(base_event)

    return expanded


def merge_calendars(
    calendar_paths: list[Path], deduplicate: bool = True
) -> list[Event]:
    """
    Merge events from multiple calendar files.

    Args:
        calendar_paths: List of paths to .ics files
        deduplicate: If True, remove duplicate events by UID

    Returns:
        List of merged events
    """
    all_events: list[Event] = []
    seen_uids: set[str] = set()

    for path in calendar_paths:
        for event in parse_ical_file(path):
            if deduplicate and event.uid in seen_uids:
                continue
            seen_uids.add(event.uid)
            all_events.append(event)

    return sorted(all_events, key=lambda e: e.start)


def find_conflicts(events: list[Event]) -> list[Conflict]:
    """
    Find all scheduling conflicts (overlapping events).

    Args:
        events: List of events to check for conflicts

    Returns:
        List of Conflict objects representing overlapping event pairs
    """
    conflicts: list[Conflict] = []
    sorted_events = sorted(events, key=lambda e: e.start)

    for i, event1 in enumerate(sorted_events):
        for event2 in sorted_events[i + 1 :]:
            # Optimization: if event2 starts after event1 ends, no more conflicts
            if event2.start >= event1.end:
                break
            if event1.overlaps(event2):
                conflicts.append(Conflict(event1, event2))

    return conflicts


def filter_events(
    events: list[Event],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search_query: str | None = None,
) -> list[Event]:
    """
    Filter events by date range and/or search query.

    Args:
        events: List of events to filter
        start_date: Include events starting on or after this date
        end_date: Include events ending on or before this date
        search_query: Filter by summary/description containing this text

    Returns:
        Filtered list of events
    """
    filtered = events

    if start_date:
        filtered = [e for e in filtered if e.start >= start_date]

    if end_date:
        filtered = [e for e in filtered if e.end <= end_date]

    if search_query:
        query_lower = search_query.lower()
        filtered = [
            e
            for e in filtered
            if query_lower in e.summary.lower() or query_lower in e.description.lower()
        ]

    return filtered


def create_merged_calendar(
    events: list[Event], calendar_name: str = "Merged Calendar"
) -> Calendar:
    """
    Create an iCalendar object from a list of events.

    Args:
        events: List of events to include
        calendar_name: Name for the merged calendar

    Returns:
        iCalendar Calendar object
    """
    cal = Calendar()
    cal.add("prodid", "-//Smart Calendar Merger//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", calendar_name)

    for event in events:
        cal.add_component(event.to_ical_event())

    return cal


def format_event(event: Event) -> str:
    """Format an event for display."""
    if event.all_day:
        time_str = event.start.strftime("%Y-%m-%d") + " (all day)"
    else:
        time_str = (
            f"{event.start.strftime('%Y-%m-%d %H:%M')} - {event.end.strftime('%H:%M')}"
        )

    location_str = f" @ {event.location}" if event.location else ""
    return f"  [{time_str}] {event.summary}{location_str}"


def format_conflict(conflict: Conflict) -> str:
    """Format a conflict for display."""
    duration_mins = int(conflict.overlap_duration.total_seconds() / 60)
    return (
        f"CONFLICT ({duration_mins} min overlap):\n"
        f"  Event 1: {conflict.event1.summary}\n"
        f"    Time: {conflict.event1.start.strftime('%Y-%m-%d %H:%M')} - "
        f"{conflict.event1.end.strftime('%H:%M')}\n"
        f"    Source: {conflict.event1.source_file}\n"
        f"  Event 2: {conflict.event2.summary}\n"
        f"    Time: {conflict.event2.start.strftime('%Y-%m-%d %H:%M')} - "
        f"{conflict.event2.end.strftime('%H:%M')}\n"
        f"    Source: {conflict.event2.source_file}"
    )


def cmd_merge(args: argparse.Namespace) -> int:
    """Handle the merge subcommand."""
    calendar_paths = _collect_calendar_paths(args)

    if not calendar_paths:
        print("Error: No calendar files specified", file=sys.stderr)
        return 1

    events = merge_calendars(calendar_paths, deduplicate=not args.no_dedupe)

    if not events:
        print("No events found in the specified calendars", file=sys.stderr)
        return 1

    merged_cal = create_merged_calendar(events)

    if args.output:
        with open(args.output, "wb") as f:
            f.write(merged_cal.to_ical())
        print(f"Merged {len(events)} events to {args.output}")
    else:
        sys.stdout.buffer.write(merged_cal.to_ical())

    return 0


def cmd_conflicts(args: argparse.Namespace) -> int:
    """Handle the conflicts subcommand."""
    calendar_paths = _collect_calendar_paths(args)

    if not calendar_paths:
        print("Error: No calendar files specified", file=sys.stderr)
        return 1

    events = merge_calendars(calendar_paths, deduplicate=True)

    # Apply date range filter if specified
    start_dt = _parse_date_arg(args.start) if args.start else None
    end_dt = _parse_date_arg(args.end) if args.end else None

    if start_dt or end_dt:
        events = filter_events(events, start_dt, end_dt)

    conflicts = find_conflicts(events)

    if args.json:
        print(json.dumps([c.to_dict() for c in conflicts], indent=2))
    else:
        if conflicts:
            print(f"Found {len(conflicts)} scheduling conflict(s):\n")
            for conflict in conflicts:
                print(format_conflict(conflict))
                print()
        else:
            print("No scheduling conflicts found")

    return 0 if conflicts else 1


def cmd_filter(args: argparse.Namespace) -> int:
    """Handle the filter subcommand."""
    calendar_paths = _collect_calendar_paths(args)

    if not calendar_paths:
        print("Error: No calendar files specified", file=sys.stderr)
        return 1

    events = merge_calendars(calendar_paths, deduplicate=True)

    start_dt = _parse_date_arg(args.start) if args.start else None
    end_dt = _parse_date_arg(args.end) if args.end else None

    filtered = filter_events(events, start_dt, end_dt, args.search)

    if not filtered:
        print("No events match the filter criteria", file=sys.stderr)
        return 1

    if args.output:
        cal = create_merged_calendar(filtered, "Filtered Events")
        with open(args.output, "wb") as f:
            f.write(cal.to_ical())
        print(f"Filtered {len(filtered)} events to {args.output}")
    elif args.json:
        print(json.dumps([e.to_dict() for e in filtered], indent=2))
    else:
        for event in filtered:
            print(format_event(event))

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the list subcommand."""
    calendar_paths = _collect_calendar_paths(args)

    if not calendar_paths:
        print("Error: No calendar files specified", file=sys.stderr)
        return 1

    events = merge_calendars(calendar_paths, deduplicate=True)

    start_dt = _parse_date_arg(args.start) if args.start else None
    end_dt = _parse_date_arg(args.end) if args.end else None

    if start_dt or end_dt:
        events = filter_events(events, start_dt, end_dt)

    if not events:
        print("No events found", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([e.to_dict() for e in events], indent=2))
    else:
        print(f"Found {len(events)} event(s):\n")
        for event in events:
            print(format_event(event))

    return 0


def _collect_calendar_paths(args: argparse.Namespace) -> list[Path]:
    """Collect calendar file paths from arguments."""
    paths: list[Path] = []

    # From positional arguments
    if hasattr(args, "calendars") and args.calendars:
        paths.extend(Path(p) for p in args.calendars)

    # From directory
    if hasattr(args, "dir") and args.dir:
        dir_path = Path(args.dir)
        if dir_path.is_dir():
            paths.extend(dir_path.glob("*.ics"))

    return [p for p in paths if p.exists() and p.suffix.lower() == ".ics"]


def _parse_date_arg(date_str: str) -> datetime:
    """Parse a date string argument to a datetime."""
    dt = parse_date(date_str)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="calendar_merger",
        description="Smart Calendar Merger - Parse, merge, and analyze iCalendar files",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge multiple calendars")
    merge_parser.add_argument("calendars", nargs="*", help="Calendar files to merge")
    merge_parser.add_argument("--dir", "-d", help="Directory containing .ics files")
    merge_parser.add_argument("--output", "-o", help="Output file path")
    merge_parser.add_argument(
        "--no-dedupe", action="store_true", help="Don't remove duplicate events"
    )
    merge_parser.set_defaults(func=cmd_merge)

    # Conflicts command
    conflicts_parser = subparsers.add_parser(
        "conflicts", help="Find scheduling conflicts"
    )
    conflicts_parser.add_argument(
        "calendars", nargs="*", help="Calendar files to check"
    )
    conflicts_parser.add_argument("--dir", "-d", help="Directory containing .ics files")
    conflicts_parser.add_argument(
        "--start", help="Start date for filtering (YYYY-MM-DD)"
    )
    conflicts_parser.add_argument("--end", help="End date for filtering (YYYY-MM-DD)")
    conflicts_parser.add_argument("--json", action="store_true", help="Output as JSON")
    conflicts_parser.set_defaults(func=cmd_conflicts)

    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter events")
    filter_parser.add_argument("calendars", nargs="*", help="Calendar files to filter")
    filter_parser.add_argument("--dir", "-d", help="Directory containing .ics files")
    filter_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    filter_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    filter_parser.add_argument(
        "--search", "-s", help="Search query for summary/description"
    )
    filter_parser.add_argument("--output", "-o", help="Output file path")
    filter_parser.add_argument("--json", action="store_true", help="Output as JSON")
    filter_parser.set_defaults(func=cmd_filter)

    # List command
    list_parser = subparsers.add_parser("list", help="List events")
    list_parser.add_argument("calendars", nargs="*", help="Calendar files to list")
    list_parser.add_argument("--dir", "-d", help="Directory containing .ics files")
    list_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    list_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
