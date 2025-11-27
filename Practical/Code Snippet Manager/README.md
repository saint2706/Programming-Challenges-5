# Code Snippet Manager

A small SQLite-backed CLI for adding, searching, and exporting code snippets with tags and terminal syntax highlighting.

## Features
- SQLite schema with `snippets`, `tags`, and `snippet_tags` tables (many-to-many tagging).
- Add snippets with arbitrary tags and store their creation timestamp.
- List, search (by keywords in title/code or by required tags), and show detailed, syntax-highlighted snippets.
- Import/export snippets to JSON for easy backup or sharing.
- Uses [Pygments](https://pygments.org/) to render highlighted code directly in the terminal.

## Installation
Install dependencies (Pygments is required for highlighting):

```bash
pip install -r requirements.txt
```

## Usage
Run commands from this directory (or provide an explicit `--db` path to place the SQLite file elsewhere):

```bash
python cli.py add "Hello World" python --code "print('hello')" --tag greeting --tag demo
python cli.py list
python cli.py search --keyword hello --tag greeting
python cli.py show 1
python cli.py export snippets.json
python cli.py import snippets.json
```

- Use `--file path/to/code.py` to read code from a file or `--file -` to read from `stdin`.
- `--keyword` and `--tag` flags can be repeated to narrow searches; all requested tags must be present on a matching snippet.
- Exports include IDs, titles, languages, code, timestamps, and tags so imports can fully recreate the dataset.
