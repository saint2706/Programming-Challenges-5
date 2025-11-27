"""
Data Import Wizard

Reads a CSV file, infers column types using pandas, generates a SQLite table
schema via SQLAlchemy, and bulk-inserts the data.
"""

import argparse
import os
import sys
from typing import Dict

import pandas as pd
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, Table, Text, create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

# Allow running as a script despite the space in folder name
sys.path.append(os.path.dirname(__file__))


def infer_sqlalchemy_type(series: pd.Series):
    """Infer a SQLAlchemy column type from a pandas Series."""
    non_null = series.dropna()
    if non_null.empty:
        return Text()

    # Numeric inference
    numeric = pd.to_numeric(non_null, errors="coerce")
    numeric_ratio = numeric.notna().mean()
    if numeric_ratio >= 0.9:
        if (numeric.dropna() % 1 == 0).all():
            return Integer()
        return Float()

    # Date/time inference
    parsed_dates = pd.to_datetime(non_null, errors="coerce")
    date_ratio = parsed_dates.notna().mean()
    if date_ratio >= 0.8:
        return DateTime()

    # Fallback to text
    return Text()


def infer_schema(df: pd.DataFrame) -> Dict[str, object]:
    """Infer SQLAlchemy types for each column in a DataFrame."""
    schema: Dict[str, object] = {}
    for column in df.columns:
        schema[column] = infer_sqlalchemy_type(df[column])
    return schema


def coerce_dataframe(df: pd.DataFrame, schema: Dict[str, object]) -> pd.DataFrame:
    """Coerce DataFrame columns to types consistent with inferred schema."""
    coerced = df.copy()
    for column, sa_type in schema.items():
        if isinstance(sa_type, Integer):
            coerced[column] = pd.to_numeric(coerced[column], errors="coerce").astype("Int64")
        elif isinstance(sa_type, Float):
            coerced[column] = pd.to_numeric(coerced[column], errors="coerce")
        elif isinstance(sa_type, DateTime):
            coerced[column] = pd.to_datetime(coerced[column], errors="coerce")
        else:
            coerced[column] = coerced[column].where(coerced[column].notna(), None).astype(object)
    return coerced


def create_table(engine, table_name: str, schema: Dict[str, object], if_exists: str = "replace") -> Table:
    """Create a SQLAlchemy table based on the inferred schema."""
    metadata = MetaData()
    inspector = inspect(engine)
    if inspector.has_table(table_name):
        if if_exists == "fail":
            raise ValueError(f"Table '{table_name}' already exists.")
        if if_exists == "replace":
            Table(table_name, MetaData(), autoload_with=engine).drop(engine)
        elif if_exists == "append":
            return Table(table_name, metadata, autoload_with=engine)
    columns = [Column(name, col_type, nullable=True) for name, col_type in schema.items()]
    table = Table(table_name, metadata, *columns)
    metadata.create_all(engine)
    return table


def insert_rows(engine, table: Table, df: pd.DataFrame):
    """Bulk insert DataFrame rows into the table."""
    prepared = df.copy()
    records = []
    for _, row in prepared.iterrows():
        record = {}
        for column, value in row.items():
            if pd.isna(value):
                record[column] = None
            elif isinstance(value, pd.Timestamp):
                record[column] = value.to_pydatetime()
            else:
                try:
                    record[column] = value.item()  # type: ignore[attr-defined]
                except Exception:  # noqa: BLE001
                    record[column] = value
        records.append(record)
    with engine.begin() as conn:
        conn.execute(table.insert(), records)


def build_table_name(csv_path: str) -> str:
    stem = os.path.splitext(os.path.basename(csv_path))[0]
    return stem.replace(" ", "_") or "imported_data"


def main():
    parser = argparse.ArgumentParser(description="Import CSV data into SQLite with inferred schema.")
    parser.add_argument("csv", help="Path to the CSV file to import")
    parser.add_argument("--db", default="data_import.db", help="SQLite database file")
    parser.add_argument("--table", help="Name of the table to create")
    parser.add_argument(
        "--if-exists",
        choices=["fail", "replace", "append"],
        default="replace",
        help="Behavior when the table already exists",
    )

    args = parser.parse_args()
    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    table_name = args.table or build_table_name(csv_path)
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to read CSV: {exc}")
        sys.exit(1)

    schema = infer_schema(df)
    coerced_df = coerce_dataframe(df, schema)

    engine = create_engine(f"sqlite:///{args.db}")
    try:
        table = create_table(engine, table_name, schema, args.if_exists)
        insert_rows(engine, table, coerced_df)
    except (SQLAlchemyError, ValueError) as exc:
        print(f"Database error: {exc}")
        sys.exit(1)

    print(f"Imported {len(coerced_df)} rows into table '{table_name}' in {args.db}")
    print("\nInferred Schema:")
    for column, col_type in schema.items():
        print(f"- {column}: {col_type}")


if __name__ == "__main__":
    main()
