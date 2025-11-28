"""Scheduling Visual Playground.

Run FCFS, SJF (non-preemptive), and Round Robin scheduling on process data and
produce Gantt charts with matplotlib or Plotly.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt

try:  # Optional Plotly support
    import plotly.express as px
except ImportError:  # pragma: no cover - Plotly is optional in this environment
    px = None


@dataclass
class Process:
    """
    Docstring for Process.
    """
    pid: str
    arrival: int
    burst: int


Schedule = List[Tuple[str, int, int]]  # (pid, start, end)


def load_processes(dataset: str) -> List[Process]:
    """Load processes from a built-in dataset name or an external file."""
    builtin = get_builtin_datasets()
    if dataset in builtin:
        return [Process(**entry) for entry in builtin[dataset]]

    path = Path(dataset)
    if not path.exists():
        raise FileNotFoundError(f"Dataset '{dataset}' not found.")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text())
        return [Process(**entry) for entry in data]

    if path.suffix.lower() == ".csv":
        import csv

        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            return [Process(pid=row["pid"], arrival=int(row["arrival"]), burst=int(row["burst"])) for row in reader]

    raise ValueError("Unsupported dataset format. Use a built-in name, JSON, or CSV file.")


def get_builtin_datasets() -> Dict[str, List[Dict[str, int]]]:
    """
    Docstring for get_builtin_datasets.
    """
    return {
        "basic": [
            {"pid": "P1", "arrival": 0, "burst": 5},
            {"pid": "P2", "arrival": 1, "burst": 3},
            {"pid": "P3", "arrival": 2, "burst": 8},
            {"pid": "P4", "arrival": 3, "burst": 6},
        ],
        "staggered": [
            {"pid": "J1", "arrival": 0, "burst": 4},
            {"pid": "J2", "arrival": 4, "burst": 2},
            {"pid": "J3", "arrival": 5, "burst": 6},
            {"pid": "J4", "arrival": 7, "burst": 3},
            {"pid": "J5", "arrival": 9, "burst": 5},
        ],
    }


def run_fcfs(processes: Iterable[Process]) -> Schedule:
    """
    Docstring for run_fcfs.
    """
    time = 0
    schedule: Schedule = []
    for proc in sorted(processes, key=lambda p: p.arrival):
        if time < proc.arrival:
            time = proc.arrival
        start = time
        end = start + proc.burst
        schedule.append((proc.pid, start, end))
        time = end
    return schedule


def run_sjf(processes: Iterable[Process]) -> Schedule:
    """
    Docstring for run_sjf.
    """
    procs = sorted(processes, key=lambda p: p.arrival)
    time = 0
    idx = 0
    schedule: Schedule = []
    ready: List[Tuple[int, int, Process]] = []  # (burst, arrival, process)
    import heapq

    while idx < len(procs) or ready:
        if not ready and time < procs[idx].arrival:
            time = procs[idx].arrival
        while idx < len(procs) and procs[idx].arrival <= time:
            heapq.heappush(ready, (procs[idx].burst, procs[idx].arrival, procs[idx]))
            idx += 1
        burst, _, proc = heapq.heappop(ready)
        start = time
        end = start + burst
        schedule.append((proc.pid, start, end))
        time = end
    return schedule


def run_rr(processes: Iterable[Process], quantum: int) -> Schedule:
    """
    Docstring for run_rr.
    """
    if quantum <= 0:
        raise ValueError("Quantum must be positive for Round Robin scheduling.")

    procs = sorted(processes, key=lambda p: p.arrival)
    remaining: Dict[str, int] = {p.pid: p.burst for p in procs}
    arrivals: Dict[str, int] = {p.pid: p.arrival for p in procs}
    ready: deque[Process] = deque()
    schedule: Schedule = []
    time = 0
    idx = 0

    while idx < len(procs) or ready:
        if not ready and idx < len(procs) and time < procs[idx].arrival:
            time = procs[idx].arrival

        while idx < len(procs) and procs[idx].arrival <= time:
            ready.append(procs[idx])
            idx += 1

        if not ready:
            break

        proc = ready.popleft()
        run_time = min(quantum, remaining[proc.pid])
        start = time
        end = start + run_time
        schedule.append((proc.pid, start, end))
        time = end
        remaining[proc.pid] -= run_time

        while idx < len(procs) and procs[idx].arrival <= time:
            ready.append(procs[idx])
            idx += 1

        if remaining[proc.pid] > 0:
            ready.append(proc)

    return schedule


def compute_metrics(schedule: Schedule, processes: Iterable[Process]) -> Dict[str, float]:
    """
    Docstring for compute_metrics.
    """
    arrivals = {p.pid: p.arrival for p in processes}
    bursts = {p.pid: p.burst for p in processes}
    completion: Dict[str, int] = {}
    for pid, _, end in schedule:
        completion[pid] = end

    waiting_times = {pid: completion[pid] - arrivals[pid] - bursts[pid] for pid in arrivals}
    turnaround_times = {pid: bursts[pid] + waiting_times[pid] for pid in bursts}

    return {
        "average_waiting": sum(waiting_times.values()) / len(waiting_times),
        "average_turnaround": sum(turnaround_times.values()) / len(turnaround_times),
    }


def to_gantt_blocks(schedule: Schedule) -> List[Dict[str, int]]:
    """
    Docstring for to_gantt_blocks.
    """
    return [
        {"Task": pid, "Start": start, "Finish": end}
        for pid, start, end in schedule
    ]


def plot_matplotlib(schedule: Schedule, title: str, output: Optional[Path] = None) -> Path:
    """
    Docstring for plot_matplotlib.
    """
    fig, ax = plt.subplots(figsize=(8, 2 + 0.3 * len(schedule)))
    colors = plt.cm.tab20.colors
    for idx, (pid, start, end) in enumerate(schedule):
        ax.barh(0, end - start, left=start, height=0.5, color=colors[idx % len(colors)], edgecolor="black")
        ax.text((start + end) / 2, 0, pid, ha="center", va="center", color="white", fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_yticks([])
    ax.set_title(title)
    ax.set_xlim(0, max(end for _, _, end in schedule) * 1.05)
    ax.grid(True, axis="x", linestyle="--", alpha=0.6)
    fig.tight_layout()

    output = output or Path(f"{title.replace(' ', '_').lower()}.png")
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_plotly(schedule: Schedule, title: str, output: Optional[Path] = None) -> Optional[Path]:
    """
    Docstring for plot_plotly.
    """
    if px is None:
        print("Plotly is not installed; skipping Plotly render.", file=sys.stderr)
        return None
    df = to_gantt_blocks(schedule)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Task", title=title)
    fig.update_yaxes(autorange="reversed")
    output = output or Path(f"{title.replace(' ', '_').lower()}_plotly.html")
    fig.write_html(str(output))
    return output


def run_algorithm(name: str, processes: List[Process], quantum: int) -> Tuple[Schedule, Dict[str, float]]:
    """
    Docstring for run_algorithm.
    """
    if name == "fcfs":
        schedule = run_fcfs(processes)
    elif name == "sjf":
        schedule = run_sjf(processes)
    elif name == "rr":
        schedule = run_rr(processes, quantum)
    else:
        raise ValueError(f"Unknown algorithm: {name}")
    metrics = compute_metrics(schedule, processes)
    return schedule, metrics


def comparison_plot(processes: List[Process], quantum: int, output_dir: Path) -> Path:
    """
    Docstring for comparison_plot.
    """
    algorithms = ["fcfs", "sjf", "rr"]
    fig, axes = plt.subplots(len(algorithms), 1, figsize=(10, 2 * len(algorithms)))
    colors = plt.cm.tab20.colors

    max_time = 0
    for idx, algo in enumerate(algorithms):
        schedule, metrics = run_algorithm(algo, processes, quantum)
        max_time = max(max_time, max(end for _, _, end in schedule))
        ax = axes[idx]
        for block_idx, (pid, start, end) in enumerate(schedule):
            ax.barh(0, end - start, left=start, height=0.5, color=colors[block_idx % len(colors)], edgecolor="black")
            ax.text((start + end) / 2, 0, pid, ha="center", va="center", color="white", fontweight="bold")
        ax.set_title(f"{algo.upper()} | avg wait {metrics['average_waiting']:.2f} | avg turnaround {metrics['average_turnaround']:.2f}")
        ax.set_yticks([])
        ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    for ax in axes:
        ax.set_xlim(0, max_time * 1.05)
        ax.set_xlabel("Time")

    fig.tight_layout()
    out_path = output_dir / "comparison_matplotlib.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description="Visualize CPU scheduling algorithms with Gantt charts.")
    parser.add_argument("--dataset", default="basic", help="Built-in dataset name or path to JSON/CSV file.")
    parser.add_argument("--algorithm", choices=["fcfs", "sjf", "rr", "all"], default="all")
    parser.add_argument("--quantum", type=int, default=2, help="Time quantum for Round Robin.")
    parser.add_argument("--output-dir", type=Path, default=Path("sample_outputs"))
    parser.add_argument("--plotly", action="store_true", help="Also write Plotly HTML charts when available.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    """
    Docstring for main.
    """
    args = parse_args(argv)
    processes = load_processes(args.dataset)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    algorithms = ["fcfs", "sjf", "rr"] if args.algorithm == "all" else [args.algorithm]

    for algo in algorithms:
        schedule, metrics = run_algorithm(algo, processes, args.quantum)
        title = f"{algo.upper()} Gantt"
        out_path = args.output_dir / f"{algo}_gantt_matplotlib.png"
        saved = plot_matplotlib(schedule, title, output=out_path)
        print(f"Saved matplotlib plot for {algo} to {saved}")
        if args.plotly:
            plot_path = args.output_dir / f"{algo}_gantt_plotly.html"
            html = plot_plotly(schedule, title, output=plot_path)
            if html:
                print(f"Saved Plotly plot for {algo} to {html}")
        print(f"Metrics for {algo.upper()}: avg waiting {metrics['average_waiting']:.2f}, avg turnaround {metrics['average_turnaround']:.2f}")

    comparison = comparison_plot(processes, args.quantum, args.output_dir)
    print(f"Saved comparison plot to {comparison}")


if __name__ == "__main__":
    main()
