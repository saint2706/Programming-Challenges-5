from __future__ import annotations

import argparse
import heapq
import math
import os
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple
import random

import matplotlib.pyplot as plt


"""
Module for simulating a single-server queue (M/M/1).
"""


@dataclass
class Event:
    """Represents a discrete event in the simulation."""
    time: float
    kind: str  # "arrival" or "departure"

    def __lt__(self, other: "Event") -> bool:
        return self.time < other.time


@dataclass
class SimulationResult:
    """Container for statistics collected during the simulation."""
    end_time: float
    arrivals: int
    served: int
    average_wait: float
    average_system_size: float
    utilization: float
    throughput: float
    wait_times: List[float]
    queue_history: List[Tuple[float, int]]


class QueueingSystemSimulator:
    """
    Simulates an M/M/1 queue using a discrete-event approach.

    Attributes:
        arrival_rate (float): Poisson arrival rate (lambda).
        service_rate (float): Exponential service rate (mu).
        random (random.Random): Random number generator instance.
    """
    def __init__(self, arrival_rate: float, service_rate: float, seed: Optional[int] = None):
        if arrival_rate <= 0 or service_rate <= 0:
            raise ValueError("Rates must be positive")
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.random = random.Random(seed)
        self.arrivals = 0
        self.served = 0
        self.busy_time = 0.0

    def _sample_interarrival(self) -> float:
        """Generate the next interarrival time from an exponential distribution."""
        return self.random.expovariate(self.arrival_rate)

    def _sample_service(self) -> float:
        """Generate a service time from an exponential distribution."""
        return self.random.expovariate(self.service_rate)

    def run(self, *, max_time: Optional[float] = None, max_customers: Optional[int] = None) -> SimulationResult:
        """
        Execute the simulation until a stopping condition is met.

        Args:
            max_time (Optional[float]): Stop after this much simulated time.
            max_customers (Optional[int]): Stop after serving this many customers.

        Returns:
            SimulationResult: Collected statistics and history.
        """
        if max_time is None and max_customers is None:
            raise ValueError("Provide max_time or max_customers to bound the simulation")

        clock = 0.0
        queue: Deque[float] = deque()
        events: List[Event] = []
        queue_history: List[Tuple[float, int]] = [(0.0, 0)]
        wait_times: List[float] = []

        server_busy = False
        num_in_system = 0
        area_under_q = 0.0
        last_time = 0.0

        first_arrival = self._sample_interarrival()
        heapq.heappush(events, Event(first_arrival, "arrival"))

        while events:
            event = heapq.heappop(events)
            if max_time is not None and event.time > max_time:
                area_under_q += num_in_system * (max_time - last_time)
                last_time = max_time
                clock = max_time
                break

            area_under_q += num_in_system * (event.time - last_time)
            clock = event.time
            last_time = clock

            if max_customers is not None and self.served >= max_customers:
                break

            if event.kind == "arrival":
                self.arrivals += 1
                next_arrival = clock + self._sample_interarrival()
                if max_time is None or next_arrival <= max_time:
                    heapq.heappush(events, Event(next_arrival, "arrival"))

                if server_busy:
                    queue.append(clock)
                else:
                    server_busy = True
                    service_time = self._sample_service()
                    self.busy_time += service_time
                    wait_times.append(0.0)
                    heapq.heappush(events, Event(clock + service_time, "departure"))
            elif event.kind == "departure":
                self.served += 1
                if queue:
                    arrival_time = queue.popleft()
                    wait = clock - arrival_time
                    wait_times.append(wait)
                    service_time = self._sample_service()
                    self.busy_time += service_time
                    heapq.heappush(events, Event(clock + service_time, "departure"))
                else:
                    server_busy = False
            else:
                raise ValueError(f"Unknown event type: {event.kind}")

            num_in_system = len(queue) + (1 if server_busy else 0)
            queue_history.append((clock, num_in_system))

            if max_customers is not None and self.served >= max_customers:
                break

        end_time = clock
        average_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0
        average_system_size = area_under_q / end_time if end_time > 0 else 0.0
        utilization = self.busy_time / end_time if end_time > 0 else 0.0
        throughput = self.served / end_time if end_time > 0 else 0.0

        return SimulationResult(
            end_time=end_time,
            arrivals=self.arrivals,
            served=self.served,
            average_wait=average_wait,
            average_system_size=average_system_size,
            utilization=utilization,
            throughput=throughput,
            wait_times=wait_times,
            queue_history=queue_history,
        )


def plot_results(result: SimulationResult, output_dir: str) -> None:
    """Generate and save plots for queue size over time and wait time distribution."""
    os.makedirs(output_dir, exist_ok=True)

    times, sizes = zip(*result.queue_history)
    plt.figure(figsize=(10, 4))
    plt.step(times, sizes, where="post")
    plt.xlabel("Time")
    plt.ylabel("Number in system")
    plt.title("System Size Over Time")
    plt.grid(True)
    queue_path = os.path.join(output_dir, "queue_over_time.png")
    plt.savefig(queue_path, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 4))
    plt.hist(result.wait_times, bins=max(10, int(math.sqrt(len(result.wait_times) + 1))), color="#1f77b4", edgecolor="black")
    plt.xlabel("Wait time")
    plt.ylabel("Frequency")
    plt.title("Wait Time Distribution")
    plt.grid(True)
    waits_path = os.path.join(output_dir, "wait_time_histogram.png")
    plt.savefig(waits_path, bbox_inches="tight")
    plt.close()

    print(f"Saved plots to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-server queue simulator with Poisson arrivals and exponential service.")
    parser.add_argument("--arrival-rate", type=float, default=3.0, help="Arrival rate (lambda) for the Poisson process.")
    parser.add_argument("--service-rate", type=float, default=4.0, help="Service rate (mu) for the exponential distribution.")
    parser.add_argument("--duration", type=float, help="Maximum simulation time. Provide duration or customers.")
    parser.add_argument("--customers", type=int, help="Number of customers to serve before stopping. Provide duration or customers.")
    parser.add_argument("--seed", type=int, default=0, help="Seed for the random number generator.")
    parser.add_argument("--output", type=str, default="results", help="Directory to store generated plots.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    simulator = QueueingSystemSimulator(
        arrival_rate=args.arrival_rate,
        service_rate=args.service_rate,
        seed=args.seed,
    )
    result = simulator.run(max_time=args.duration, max_customers=args.customers)

    print("--- Simulation Summary ---")
    print(f"End time: {result.end_time:.2f}")
    print(f"Arrivals: {result.arrivals}")
    print(f"Served: {result.served}")
    print(f"Average wait time: {result.average_wait:.3f}")
    print(f"Average number in system: {result.average_system_size:.3f}")
    print(f"Utilization: {result.utilization:.3f}")
    print(f"Throughput: {result.throughput:.3f}")

    plot_results(result, args.output)


if __name__ == "__main__":
    main()
