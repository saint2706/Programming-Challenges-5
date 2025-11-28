# Media Library Organizer

Organizes your movie collection by fetching metadata from The Movie Database (TMDB).

## Requirements

- Python 3.8+
- `requests`
- A TMDB API Key

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

You must set the `TMDB_API_KEY` environment variable.

```bash
export TMDB_API_KEY="your_api_key_here"
```

## Usage

```bash
python "Practical/Media Library Organizer/__main__.py" --source ./downloads --target ./movies
```

## Features

- Scans a directory for video files (`.mp4`, `.mkv`, `.avi`).
- Guesses the title and year from the filename.
- Queries TMDB for correct metadata.
- Moves the file to a structured format: `Target/Title (Year)/Title (Year).ext`.
