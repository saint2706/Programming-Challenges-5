# Terminal Habit Coach

A command-line assistant for tracking habits, logging progress, and monitoring streaks directly from the terminal.

## 📋 Features

- **Local Persistence**: SQLite-backed storage for habits, log entries, and streak metadata.
- **CLI Interface**: Commands for adding habits, logging progress, checking status tables, and inspecting streaks.
- **Reminders**: Helper that lists habits with a reminder time that have not been logged today.
- **Statistics**: Friendly summaries per habit showing counts and streak history.

## 💻 Installation

The package is self-contained inside this repository. You can run the CLI using Python's module execution:

```bash
python -m Practical.TerminalHabitCoach.cli --help
```

For daily usage, consider creating an alias:

```bash
alias thc="python -m Practical.TerminalHabitCoach.cli"
```

## 🚀 Usage

### Add a Habit
```bash
thc add-habit "Morning Walk" --description "15 minute walk" --reminder 07:30
```

### Log Progress
Log for now:
```bash
thc log "Morning Walk"
```

Log for a specific time with a note:
```bash
thc log "Morning Walk" --when 2024-05-01T07:20:00 --note "Sunny day"
```

### Check Status
View a table of all habits and today's reminders:
```bash
thc status
```

### View Streaks
Inspect streak health:
```bash
thc streaks
```

### Habit Details
Display an individual summary with recent log entries:
```bash
thc show "Morning Walk"
```

## 💾 Database

By default the database lives at `~/.terminal_habit_coach.db`.

Override the path using `--database` when invoking the CLI:
```bash
thc --database /tmp/habits.db status
```

## 🧪 Testing

The repository ships with pytest-based tests. Run them from the project root:

```bash
pytest
```
