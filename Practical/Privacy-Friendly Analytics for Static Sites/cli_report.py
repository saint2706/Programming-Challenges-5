"""CLI for aggregating page view counts by URL and date."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime
from typing import Iterable, Tuple

from sqlalchemy import func, select

if __package__:
    from .db import DATABASE_URL, SessionLocal, engine
    from .models import PageView
else:  # Enable running as a script despite spaces in folder name
    sys.path.append(os.path.dirname(__file__))
    from db import DATABASE_URL, SessionLocal, engine  # type: ignore
    from models import PageView  # type: ignore


def ensure_schema() -> None:
    if __package__:
        from .db import Base
    else:
        from db import Base  # type: ignore

    Base.metadata.create_all(bind=engine)


def parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_counts(
    start: date | None, end: date | None
) -> Iterable[Tuple[date, str, int]]:
    ensure_schema()
    with SessionLocal() as session:
        date_column = func.date(PageView.timestamp).label("day")
        stmt = select(date_column, PageView.url, func.count(PageView.id)).group_by(
            date_column, PageView.url
        )

        if start:
            stmt = stmt.where(date_column >= start)
        if end:
            stmt = stmt.where(date_column <= end)

        stmt = stmt.order_by(date_column.desc(), PageView.url)
        for day, url, count in session.execute(stmt):
            yield day, url, count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize page views per URL and date"
    )
    parser.add_argument(
        "--start-date", dest="start", help="Filter results from this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", dest="end", help="Filter results up to this date (YYYY-MM-DD)"
    )
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)

    print(f"Using database at {DATABASE_URL}")
    print("Day         | Count | URL")
    print("------------+-------+------------------------------------------")

    for day, url, count in fetch_counts(start, end):
        print(f"{day} | {count:5d} | {url}")


if __name__ == "__main__":
    main()
