# Practical – Screen Time Tracker

A cross-platform focus tracker that watches the active window title and records how long each application is in the foreground. Storage can be SQLite or JSON, and summaries are available via CLI or a lightweight Tkinter GUI.

## Features

- Abstracted OS support: pywin32 on Windows, AppleScript on macOS, X11/EWMH (or `xprop` fallback) on Linux.
- Scheduler loop that records focus intervals at a configurable polling rate.
- Summaries of per-application usage for any day.
- CLI for starting the tracker and printing daily reports.
- Optional GUI for at-a-glance daily totals.

## Usage

```bash
# Start logging with SQLite (default)
python -m "Practical.Screen Time Tracker.cli" track --interval 5

# Use JSON storage instead
python -m "Practical.Screen Time Tracker.cli" track --backend json --path my_log.json

# Show today's summary
python -m "Practical.Screen Time Tracker.cli" summary --date today

# Launch the Tkinter GUI (reads the same storage file)
python -m "Practical.Screen Time Tracker.gui"
```

Platform-specific dependencies are loaded lazily. For active window detection you may need:

- Windows: `pip install pywin32 psutil`
- macOS: built-in `osascript`
- Linux: `pip install ewmh` or have `xprop` available in `PATH`
