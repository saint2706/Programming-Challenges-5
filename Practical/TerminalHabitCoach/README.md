# Terminal Habit Coach

A command-line assistant for tracking habits, logging progress, and monitoring streaks directly from the terminal.

## Features

- SQLite-backed storage for habits, log entries, and streak metadata.
- Commands for adding habits, logging progress, checking status tables, and inspecting streaks.
- Reminder helper that lists habits with a reminder time that have not been logged today.
- Friendly summaries per habit showing statistics and recent history.

## Installation

The package is self-contained inside this repository. You can run the CLI using Python's module execution:

```bash
python -m Practical.TerminalHabitCoach.cli --help
```

For daily usage, consider creating an alias:

```bash
alias thc="python -m Practical.TerminalHabitCoach.cli"
```

## Usage

Add a habit:

```bash
thc add-habit "Morning Walk" --description "15 minute walk" --reminder 07:30
```

Log progress (now or at a specific timestamp):

```bash
thc log "Morning Walk"
thc log "Morning Walk" --when 2024-05-01T07:20:00 --note "Sunny day"
```

Check current status and reminders:

```bash
thc status
```

Inspect streak health:

```bash
thc streaks
```

Display an individual summary with recent log entries:

```bash
thc show "Morning Walk"
```

## Database

By default the database lives at `~/.terminal_habit_coach.db`. Override the path using `--database /tmp/habits.db` when invoking the CLI (useful for testing or scripting).

## Testing

The repository ships with pytest-based tests. Run them from the project root:

```bash
pytest
```
