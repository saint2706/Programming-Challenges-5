# Personal Finance Dashboard

A Streamlit web app that ingests personal finance CSV exports and turns them into interactive visualizations. Upload your transaction history and explore spending trends over time with category breakdowns and filters.

## Features
- CSV ingestion with smart column detection (date, amount, category, description).
- Date range and category filters in the sidebar.
- Interactive Plotly charts for spending over time and category distribution (bar + pie).
- Summary metrics for total spend, average daily spend, and top category.
- View of filtered raw transactions for quick inspection.

## Requirements
- Python 3.9+
- See `requirements.txt` for Python dependencies.

## Installation
```bash
pip install -r "Practical/Personal Finance Dashboard/requirements.txt"
```

## Usage
Run the Streamlit app from the repository root:
```bash
streamlit run "Practical/Personal Finance Dashboard/app.py"
```

Upload a CSV that includes columns for date, amount, and category (a description/memo column is optional). The app will normalize common column names automatically.
