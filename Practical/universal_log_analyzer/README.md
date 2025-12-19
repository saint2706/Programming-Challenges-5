# Universal Log Analyzer

A command-line tool to parse common access logs (Apache/Nginx style) and generate a visual report.

## Requirements

- Python 3.8+
- `pandas`
- `matplotlib`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m Practical.universal_log_analyzer path/to/access.log --output my_report.png
```

## Features

- Parses Common Log Format (CLF).
- Generates a PNG report with:
  - Requests per hour.
  - Top 5 requested paths.
  - HTTP Status code distribution.
