# Scheduling Visual Playground

A lightweight playground to explore **FCFS**, **SJF (non-preemptive)**, and **Round Robin** CPU scheduling. Feed in process arrival/burst data, run the algorithms, and generate Gantt charts with matplotlib (and optionally Plotly) for quick visual comparisons.

## Features
- Built-in sample datasets plus support for JSON/CSV inputs.
- FCFS, SJF, and RR implementations that return detailed schedules and average waiting/turnaround metrics.
- Matplotlib PNG outputs by default; optional Plotly HTML timelines when Plotly is available.
- Comparison plot that stacks all algorithms with their average metrics for side-by-side inspection.

## Getting Started
1. Ensure Python 3 with `matplotlib`. Plotly output is optional and only needed for HTML charts (`pip install plotly`).
2. Run the script from this directory (or provide the full path):
   ```bash
   python scheduling_visual_playground.py --dataset basic --algorithm all --quantum 2 --output-dir sample_outputs --plotly
   ```
   The command saves a matplotlib Gantt chart for each algorithm, an optional Plotly HTML version, and a combined comparison plot under `sample_outputs/`.

### Parameters
- `--dataset`: Built-in dataset name (`basic`, `staggered`) or a path to a JSON/CSV file with `pid,arrival,burst` columns.
- `--algorithm`: One of `fcfs`, `sjf`, `rr`, or `all` to run every algorithm.
- `--quantum`: Time quantum for Round Robin (ignored by other algorithms).
- `--output-dir`: Where to write generated plots.
- `--plotly`: When set, also emits Plotly HTML charts if Plotly is installed.

## Built-in Datasets
- **basic**: Four processes arriving back-to-back with varied burst times.
- **staggered**: Processes spaced out over time to highlight idle gaps and Round Robin preemption.

You can also supply your own JSON/CSV file with a structure like:
```json
[
  { "pid": "A", "arrival": 0, "burst": 4 },
  { "pid": "B", "arrival": 1, "burst": 2 },
  { "pid": "C", "arrival": 2, "burst": 7 }
]
```

## Sample Outputs
Running the "basic" dataset with a quantum of 2 produces a comparison chart plus one Gantt chart per algorithm under `sample_outputs/` (ignored in git to avoid committing binaries). Expected files:

- `comparison_matplotlib.png`
- `fcfs_gantt_matplotlib.png`
- `sjf_gantt_matplotlib.png`
- `rr_gantt_matplotlib.png`

These outputs show execution order, preemption (for RR), and how average waiting/turnaround times differ across strategies. Use them as a starting point to plug in your own workloads and regenerate visuals locally.
