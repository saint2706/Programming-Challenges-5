"""Streamlit dataset explorer app.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dataset Explorer", layout="wide")


def load_dataframe(uploaded_file: Optional[st.runtime.uploaded_file_manager.UploadedFile],
                   file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a dataframe from an uploaded file or a provided path.

    Returns a tuple of (dataframe, error_message).
    """
    try:
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file), None
        if file_path:
            expanded_path = Path(os.path.expanduser(file_path))
            if not expanded_path.exists():
                return None, f"File not found: {expanded_path}"
            return pd.read_csv(expanded_path), None
        return None, "Please upload a CSV or provide a valid file path."
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"Error loading data: {exc}"


def render_distribution_plots(df: pd.DataFrame, numeric_columns: list[str]) -> None:
    if not numeric_columns:
        st.info("No numeric columns available for distribution plots.")
        return

    selected = st.multiselect(
        "Select numeric columns for distribution plots",
        numeric_columns,
        default=numeric_columns[: min(3, len(numeric_columns))],
    )
    if not selected:
        st.info("Select at least one column to see distributions.")
        return

    for column in selected:
        fig, ax = plt.subplots()
        sns.histplot(df[column].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution of {column}")
        st.pyplot(fig)
        plt.close(fig)


def render_correlation_heatmap(df: pd.DataFrame, numeric_columns: list[str]) -> None:
    if len(numeric_columns) < 2:
        st.info("Need at least two numeric columns to compute correlations.")
        return

    corr = df[numeric_columns].corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Heatmap")
    st.pyplot(fig)
    plt.close(fig)


def generate_pandas_profile(df: pd.DataFrame) -> Optional[bytes]:
    try:
        from ydata_profiling import ProfileReport
    except ImportError:
        st.warning("ydata-profiling not installed. Install to enable this feature.")
        return None

    profile = ProfileReport(df, title="Pandas Profiling Report", explorative=True)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        profile.to_file(tmp_file.name)
        tmp_file.seek(0)
        html_bytes = tmp_file.read()
    return html_bytes


def generate_sweetviz_report(df: pd.DataFrame) -> Optional[bytes]:
    try:
        import sweetviz as sv
    except ImportError:
        st.warning("sweetviz not installed. Install to enable this feature.")
        return None

    report = sv.analyze(df)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        report.show_html(filepath=tmp_file.name, open_browser=False)
        tmp_file.seek(0)
        html_bytes = tmp_file.read()
    return html_bytes


def main() -> None:
    st.title("Dataset Explorer UI")
    st.write(
        "Upload a CSV or provide a file path to explore datasets, review summary statistics, and generate insights."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    with col2:
        file_path = st.text_input("Or provide a CSV file path")

    df, error = load_dataframe(uploaded_file, file_path)
    if error:
        st.error(error)
        st.stop()
    if df is None:
        st.info("Awaiting data input.")
        st.stop()

    st.success(f"Loaded dataset with {df.shape[0]} rows and {df.shape[1]} columns.")

    if st.checkbox("Show raw data", value=True):
        st.dataframe(df.head(100))

    st.subheader("Summary Statistics")
    st.write(df.describe(include="all"))

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    st.subheader("Distribution Plots")
    render_distribution_plots(df, numeric_columns)

    st.subheader("Correlation Heatmap")
    render_correlation_heatmap(df, numeric_columns)

    st.subheader("Optional Profiling Reports")
    st.write(
        "These reports can be slow on large datasets. Toggle on to generate them when needed."
    )
    col_profile, col_sweetviz = st.columns(2)

    with col_profile:
        if st.toggle("Generate pandas-profiling report"):
            profile_html = generate_pandas_profile(df)
            if profile_html:
                st.download_button(
                    "Download pandas-profiling report",
                    data=profile_html,
                    file_name="pandas_profiling_report.html",
                    mime="text/html",
                )
                st.success("Report ready for download.")

    with col_sweetviz:
        if st.toggle("Generate Sweetviz report"):
            sweetviz_html = generate_sweetviz_report(df)
            if sweetviz_html:
                st.download_button(
                    "Download Sweetviz report",
                    data=sweetviz_html,
                    file_name="sweetviz_report.html",
                    mime="text/html",
                )
                st.success("Report ready for download.")


if __name__ == "__main__":
    main()
