# Personal Time Tracker

A simple command line tool that lets you record work sessions, store them in a
JSON data file, and produce daily or weekly reports.

## 📋 Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Storage](#storage)

## 💻 Installation

The package lives inside this repository. Run the commands from the repository
root.

Ensure you have Python 3.8+ installed.

## 🚀 Usage

### Help
View all available commands:
```bash
python -m Practical.PersonalTimeTracker --help
```

### Start a Session
Start a timer for a specific category. You can optionally add notes.

```bash
python -m Practical.PersonalTimeTracker start --category coding --notes "Morning feature work"
```

### Stop a Session
Stop the currently active session. You can append more notes upon stopping.

```bash
python -m Practical.PersonalTimeTracker stop --notes "Done with the feature"
```

### List Sessions
View a chronological list of all recorded sessions.

```bash
python -m Practical.PersonalTimeTracker list
```

### Reports
Generate aggregated reports of time spent per category.

**Daily Report:**
```bash
python -m Practical.PersonalTimeTracker report --period daily
```

**Weekly Report:**
```bash
python -m Practical.PersonalTimeTracker report --period weekly
```

## 💾 Storage

Sessions are stored in a JSON file at `~/.personal_time_tracker/sessions.json` by
default.

### Custom Location
You can override the storage location by setting the `PTT_DB_PATH` environment variable. This is useful for testing or maintaining separate databases.

```bash
export PTT_DB_PATH="./my_sessions.json"
python -m Practical.PersonalTimeTracker list
```
