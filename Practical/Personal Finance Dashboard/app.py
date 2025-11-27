"""Personal Finance Dashboard using Streamlit.

A web-based dashboard for analyzing personal spending data from CSV exports.
Supports columns like date, amount, category, and description. Features
interactive filters and visualizations including spending trends, category
breakdowns, and summary metrics.

Run with:
    streamlit run app.py
"""
import io

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Personal Finance Dashboard", layout="wide")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names from various CSV formats.

    Maps common column name variants to standard names (date, amount, category).

    Args:
        df: DataFrame with original column names.

    Returns:
        pd.DataFrame: DataFrame with standardized column names.
    """
    renamed = {col: col.strip().lower() for col in df.columns}
    df = df.rename(columns=renamed)

    name_map = {}
    for candidate in ("date", "transaction_date", "posted_date", "time"):
        if candidate in df.columns:
            name_map[candidate] = "date"
            break

    for candidate in ("amount", "value", "total", "spend", "spent"):
        if candidate in df.columns:
            name_map[candidate] = "amount"
            break

    for candidate in ("category", "tag", "group"):
        if candidate in df.columns:
            name_map[candidate] = "category"
            break

    if "description" in df.columns:
        name_map["description"] = "description"
    elif "memo" in df.columns:
        name_map["memo"] = "description"

    return df.rename(columns=name_map)


def load_csv(upload: io.BytesIO) -> pd.DataFrame:
    """Load and validate a CSV file with transaction data.

    Args:
        upload: File-like object containing CSV data.

    Returns:
        pd.DataFrame: Cleaned DataFrame with date, amount, category columns.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_csv(upload)
    df = _rename_columns(df)

    missing = {col for col in ("date", "amount", "category") if col not in df.columns}
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing)) + ". "
            "Include columns for date, amount, and category."
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date", "amount", "category"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    df["category"] = df["category"].astype(str)

    return df.sort_values("date").reset_index(drop=True)


def add_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Add sidebar filters for date range and categories.

    Args:
        df: DataFrame to filter.

    Returns:
        pd.DataFrame: Filtered DataFrame based on user selections.
    """
    st.sidebar.header("Filters")

    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique()),
    )

    filtered = df.copy()
    filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]

    return filtered


def render_metrics(df: pd.DataFrame) -> None:
    """Display summary metrics for the filtered transactions."""
    total_spend = df["amount"].sum()
    avg_daily = df.groupby("date")["amount"].sum().mean()
    top_category = (
        df.groupby("category")["amount"].sum().sort_values(ascending=False).head(1)
    )
    top_category_name = top_category.index[0] if not top_category.empty else "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total spend", f"${total_spend:,.2f}")
    col2.metric("Average per day", f"${avg_daily:,.2f}")
    col3.metric("Top category", top_category_name)


def render_spending_over_time(df: pd.DataFrame) -> None:
    """Render a line chart showing spending over time."""
    daily = df.groupby("date")["amount"].sum().reset_index()
    fig = px.line(daily, x="date", y="amount", title="Spending over time")
    fig.update_traces(mode="markers+lines")
    fig.update_layout(yaxis_title="Amount", xaxis_title="Date")
    st.plotly_chart(fig, use_container_width=True)


def render_category_breakdown(df: pd.DataFrame) -> None:
    """Render bar and pie charts showing spending by category."""
    grouped = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    summary = grouped.reset_index(name="amount")

    col1, col2 = st.columns(2)
    bar_fig = px.bar(summary, x="category", y="amount", title="Spending by category")
    bar_fig.update_layout(xaxis_title="Category", yaxis_title="Amount")
    col1.plotly_chart(bar_fig, use_container_width=True)

    pie_fig = px.pie(summary, names="category", values="amount", title="Category share")
    col2.plotly_chart(pie_fig, use_container_width=True)


def main() -> None:
    """Main entry point for the Streamlit dashboard."""
    st.title("Personal Finance Dashboard")
    st.write(
        "Upload CSV exports from your bank, credit card, or budgeting app. "
        "The dashboard supports columns like date, amount, category, and description, "
        "and lets you explore spending trends by time range and category."
    )

    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    if not uploaded:
        st.info("Upload a CSV to begin exploring your spending data.")
        return

    try:
        df = load_csv(uploaded)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unable to load file: {exc}")
        return

    st.success(
        f"Loaded {len(df):,} transactions spanning {df['date'].min()} to {df['date'].max()}"
    )

    filtered_df = add_sidebar_filters(df)

    st.subheader("Summary")
    render_metrics(filtered_df)

    st.subheader("Spending over time")
    render_spending_over_time(filtered_df)

    st.subheader("Category breakdown")
    render_category_breakdown(filtered_df)

    with st.expander("Raw transactions"):
        st.dataframe(filtered_df.reset_index(drop=True))


if __name__ == "__main__":
    main()
