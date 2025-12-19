"""
Universal Log Analyzer

A CLI tool to parse Apache/Nginx access logs, aggregate statistics using pandas,
and generate visualization plots.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd

# Common Log Format (CLF) regex
# 127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
LOG_PATTERN = re.compile(
    r'(?P<ip>[\d\.]+) - - \[(?P<datetime>[^\]]+)\] "(?P<method>\w+) (?P<path>.*?) (?P<protocol>.*?)" (?P<status>\d+) (?P<size>\d+|-)'
)


def parse_log_line(line: str) -> Optional[Dict]:
    """Parse a single log line using regex."""
    match = LOG_PATTERN.match(line)
    if not match:
        return None
    data = match.groupdict()
    # Convert size to int, handle '-'
    data["size"] = int(data["size"]) if data["size"] != "-" else 0
    # Parse datetime
    # Example: 10/Oct/2000:13:55:36 -0700
    try:
        dt_str = data["datetime"].split(" ")[
            0
        ]  # simpler handling, ignoring timezone for basic aggregation if needed
        data["timestamp"] = datetime.strptime(dt_str, "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        return None  # Skip malformed dates
    return data


def analyze_logs(file_path: str, output_image: str):
    """Read logs, aggregate data, and generate a report plot."""
    records = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed:
                    records.append(parsed)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    if not records:
        print("No valid log lines found.")
        return

    df = pd.DataFrame(records)

    # 1. Requests per hour
    df["hour"] = df["timestamp"].dt.hour
    requests_per_hour = df.groupby("hour").size()

    # 2. Top 5 Paths
    top_paths = df["path"].value_counts().head(5)

    # 3. Status Codes
    status_counts = df["status"].value_counts()

    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))
    fig.suptitle(f"Log Analysis Report: {file_path}")

    # Hourly Traffic
    axes[0].bar(requests_per_hour.index, requests_per_hour.values, color="skyblue")
    axes[0].set_title("Requests per Hour")
    axes[0].set_xlabel("Hour of Day")
    axes[0].set_ylabel("Count")
    axes[0].set_xticks(range(0, 24))

    # Top Paths
    axes[1].barh(top_paths.index, top_paths.values, color="lightgreen")
    axes[1].set_title("Top 5 Paths")
    axes[1].invert_yaxis()  # Highest at top

    # Status Codes
    axes[2].pie(
        status_counts.values,
        labels=status_counts.index,
        autopct="%1.1f%%",
        startangle=140,
    )
    axes[2].set_title("Status Code Distribution")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_image)
    print(f"Analysis complete. Report saved to {output_image}")

    # Text Summary
    print("\n--- Summary ---")
    print(f"Total Requests: {len(df)}")
    print(f"Total Data Transfer: {df['size'].sum() / 1024 / 1024:.2f} MB")
    print("\nTop Paths:")
    print(top_paths)


def main():
    parser = argparse.ArgumentParser(description="Universal Log Analyzer")
    parser.add_argument("logfile", help="Path to the access log file")
    parser.add_argument(
        "--output", default="report.png", help="Path to save the output image"
    )

    args = parser.parse_args()
    analyze_logs(args.logfile, args.output)


if __name__ == "__main__":
    main()
