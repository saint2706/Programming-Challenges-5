# Personal Time Tracker

A simple command line tool that lets you record work sessions, store them in a
JSON data file, and produce daily or weekly reports.

## Installation

The package lives inside this repository. Run the commands from the repository
root:

```bash
python -m Practical.PersonalTimeTracker --help
```

## Usage

Start a session by providing a category and optional notes:

```bash
python -m Practical.PersonalTimeTracker start --category coding --notes "Morning feature work"
```

Stop the current session:

```bash
python -m Practical.PersonalTimeTracker stop --notes "Done with the feature"
```

List recorded sessions:

```bash
python -m Practical.PersonalTimeTracker list
```

Generate reports:

```bash
python -m Practical.PersonalTimeTracker report --period daily
python -m Practical.PersonalTimeTracker report --period weekly
```

## Storage

Sessions are stored in a JSON file at `~/.personal_time_tracker/sessions.json` by
default. Set the `PTT_DB_PATH` environment variable to override the location –
handy for testing or keeping separate databases for work and personal tasks.
