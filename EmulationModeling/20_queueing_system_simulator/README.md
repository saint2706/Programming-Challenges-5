# Queueing System Simulator

This module implements a single-server queue simulator with Poisson arrivals and exponential service times. It uses a discrete-event loop to handle arrivals and departures, tracking queue length over time and the wait experienced by each customer. Runs can be bounded by elapsed simulation time or by the number of customers served, and simulations are reproducible through a configurable seed.

## Requirements

- Python 3.9+
- `matplotlib` for generating plots (install via `pip install matplotlib`).

## Usage

Run the simulator directly:

```bash
python simulator.py --arrival-rate 3.0 --service-rate 4.0 --duration 200 --seed 42 --output results
```

Key options:

- `--arrival-rate`: Poisson arrival rate \(\lambda\) (default: 3.0).
- `--service-rate`: Exponential service rate \(\mu\) (default: 4.0).
- `--duration`: Maximum simulation time. Provide this or `--customers`.
- `--customers`: Number of customers to serve before stopping. Provide this or `--duration`.
- `--seed`: Seed for the RNG to obtain reproducible runs (default: 0).
- `--output`: Directory for generated plots (default: `results`).

Example stopping after a set number of customers:

```bash
python simulator.py --arrival-rate 2.5 --service-rate 3.0 --customers 500 --seed 1 --output customers_run
```

## Outputs

The script prints summary statistics, including average wait time, average number in the system, utilization, and throughput. It also writes two plots to the output directory:

- `queue_over_time.png`: Step plot of the system size (queue + any job in service).
- `wait_time_histogram.png`: Distribution of observed wait times.

These outputs make it easy to experiment with different arrival and service rates while keeping runs reproducible.
