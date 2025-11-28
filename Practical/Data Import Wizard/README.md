# Data Import Wizard

A command-line utility that reads a CSV file, infers column data types with `pandas`, and builds a SQLite table using SQLAlchemy before bulk-inserting the data.

## Requirements

- Python 3.9+
- pandas
- SQLAlchemy

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m Practical.DataImportWizard path/to/data.csv --db data_import.db --table imported_data --if-exists replace
```

Options:

- `--db`: Path to the SQLite database file (default: `data_import.db`).
- `--table`: Name of the target table (default: CSV filename without extension).
- `--if-exists`: How to handle existing tables: `fail`, `replace`, or `append` (default: `replace`).

## Features

- Infers column types (integer, float, text, date) using `pandas` heuristics.
- Generates a SQLite schema with SQLAlchemy and creates the table.
- Bulk-inserts CSV rows while converting values to appropriate Python types.
- Provides a summary of inferred schema and inserted row count.
