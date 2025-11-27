# Local Search Engine

A Python-powered crawler and search engine for local documents. It indexes files from configured directories, extracts text from common formats, and uses Whoosh to provide ranked keyword search with contextual snippets.

## Features
- Recursively traverse configured directories with glob-based ignore rules.
- Extract text from `.txt`, `.md`, `.rtf`, `.pdf` (PyMuPDF with optional Tika fallback), and `.docx` files.
- On-disk Whoosh index that stores file paths, modified timestamps, and searchable content snippets.
- Incremental reindexing detects changed or removed files and updates the index accordingly.
- Parallel parsing to speed up indexing large datasets.
- CLI commands for full indexing, selective reindexing, and keyword search.

## Setup
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy and adjust the configuration template:
   ```bash
   cp config.example.yaml config.yaml
   ```

### Configuration
`config.yaml` controls where the crawler looks and how the index behaves.

```yaml
# Directories to crawl (can be absolute or relative paths)
roots:
  - ./documents

# Where the Whoosh index is stored
index_dir: ./.local_index

# Glob patterns to skip
ignored:
  - "**/.git/**"
  - "**/__pycache__/**"
  - "*.log"
  - "*.tmp"

# Parallel workers used for parsing
max_workers: 4

# Maximum characters shown in snippets
snippet_length: 240

# Use Apache Tika for PDF extraction when PyMuPDF fails or is unavailable
use_tika: false
```

## Usage
All commands are run from the `Practical/Local Search Engine` directory. Add `--verbose` to any command for detailed logging.

### Build the index
Crawl configured directories and (re)build the index:
```bash
python search_engine.py index --config config.yaml
```

### Incremental reindex
Update changed files and remove deleted ones without touching unchanged entries:
```bash
python search_engine.py reindex --config config.yaml
```

### Search
Run a keyword search with ranked results and context snippets:
```bash
python search_engine.py search "deep learning" --config config.yaml --limit 5
```

Sample output:
```
Path: /home/user/documents/papers/intro.pdf
Modified: 2024-06-01 10:34:12
Snippet: deep learning models have achieved... the dataset.
```

## Notes
- PyMuPDF is used by default for PDF parsing. Enable `use_tika: true` if you prefer Apache Tika or need a fallback when PyMuPDF cannot parse a document (requires Java if using the Tika server mode).
- Only files with supported extensions are indexed. Adjust the `SUPPORTED_EXTENSIONS` set in `search_engine.py` to add more types.
- The index directory is safe to delete; it will be recreated on the next `index` run.
