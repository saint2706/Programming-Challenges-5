# Smart Calendar Merger

A Python CLI tool for parsing, merging, and analyzing `.ics` (iCalendar) files. It can combine events from multiple calendars, detect scheduling conflicts (overlaps), and generate merged output files.

## Features

- **Parse iCalendar files**: Full support for `.ics` format using the `icalendar` library
- **Merge multiple calendars**: Combine events from any number of calendar sources
- **Conflict detection**: Find overlapping events across all calendars with detailed reports
- **Flexible output**: Export merged calendar to a new `.ics` file
- **Event filtering**: Filter events by date range or search query
- **Deduplication**: Optionally remove duplicate events based on UID or content

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Merge calendars

```bash
# Merge two or more calendars
python calendar_merger.py merge cal1.ics cal2.ics -o merged.ics

# Merge all .ics files in a directory
python calendar_merger.py merge --dir ./calendars -o merged.ics
```

### Find conflicts/overlaps

```bash
# Detect all scheduling conflicts
python calendar_merger.py conflicts cal1.ics cal2.ics

# Find conflicts within a date range
python calendar_merger.py conflicts cal1.ics cal2.ics \
    --start 2024-01-01 --end 2024-12-31
```

### Filter events

```bash
# Filter events by date range
python calendar_merger.py filter cal.ics \
    --start 2024-06-01 --end 2024-06-30 \
    -o june_events.ics

# Search events by summary/description
python calendar_merger.py filter cal.ics --search "Meeting" -o meetings.ics
```

### List events

```bash
# List all events in a calendar
python calendar_merger.py list cal.ics

# List events in a date range
python calendar_merger.py list cal.ics --start 2024-01-01 --end 2024-01-31
```

## Output Formats

- **ICS**: Standard iCalendar format for import into any calendar application
- **JSON**: Structured output for programmatic processing (use `--json` flag)
- **Text**: Human-readable conflict reports (default for `conflicts` command)

## Examples

### Combining work and personal calendars

```bash
python calendar_merger.py merge work.ics personal.ics -o combined.ics
python calendar_merger.py conflicts work.ics personal.ics
```

### Finding free time slots

The conflict detection can help identify busy periods when planning meetings across multiple team members' calendars.

## Exit Codes

- `0`: Success (or conflicts found when expected)
- `1`: No events/conflicts found or error occurred

## Notes

- Recurring events are expanded within the specified date range for accurate conflict detection
- All-day events are treated separately from timed events
- Timezone-aware and naive datetime handling is supported
