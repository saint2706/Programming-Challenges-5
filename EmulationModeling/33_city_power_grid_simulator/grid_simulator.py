"""City Power Grid Simulator

A simplified educational simulator that models an electrical grid as a graph.
Generators supply power, consumers draw power, and transmission lines have
capacity limits. Overloaded lines fail, causing power to be rerouted and
potentially leading to cascading outages.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Node:
    """Represents a grid node which can be a generator or a consumer."""

    name: str
    generation: float = 0.0
    demand: float = 0.0

    def surplus(self) -> float:
        """
        Docstring for surplus.
        """
        return max(0.0, self.generation - self.demand)

    def deficit(self) -> float:
        """
        Docstring for deficit.
        """
        return max(0.0, self.demand - self.generation)


@dataclass
class Line:
    """Represents a transmission line between two nodes."""

    a: str
    b: str
    capacity: float
    name: Optional[str] = None
    online: bool = True

    def id(self) -> str:
        """
        Docstring for id.
        """
        return self.name or f"{self.a}-{self.b}"

    def endpoints(self) -> Tuple[str, str]:
        """
        Docstring for endpoints.
        """
        return self.a, self.b


@dataclass
class FlowResult:
    """
    Docstring for FlowResult.
    """
    flows: Dict[str, float] = field(default_factory=dict)
    unmet_demand: Dict[str, float] = field(default_factory=dict)
    failed_lines: List[str] = field(default_factory=list)


class PowerGrid:
    """
    Docstring for PowerGrid.
    """
    def __init__(self) -> None:
        """
        Docstring for __init__.
        """
        self.nodes: Dict[str, Node] = {}
        self.lines: Dict[str, Line] = {}
        self.adj: Dict[str, List[str]] = {}

    def add_generator(self, name: str, generation: float) -> None:
        """
        Docstring for add_generator.
        """
        self.nodes[name] = Node(name=name, generation=generation, demand=0.0)
        self.adj.setdefault(name, [])

    def add_consumer(self, name: str, demand: float) -> None:
        """
        Docstring for add_consumer.
        """
        self.nodes[name] = Node(name=name, generation=0.0, demand=demand)
        self.adj.setdefault(name, [])

    def add_line(self, a: str, b: str, capacity: float, name: Optional[str] = None) -> None:
        """
        Docstring for add_line.
        """
        if a not in self.nodes or b not in self.nodes:
            raise ValueError("Both endpoints must be added as nodes before connecting them.")
        line = Line(a=a, b=b, capacity=capacity, name=name)
        self.lines[line.id()] = line
        self.adj.setdefault(a, []).append(b)
        self.adj.setdefault(b, []).append(a)

    def _ensure_balance(self) -> None:
        """
        Docstring for _ensure_balance.
        """
        total_generation = sum(node.generation for node in self.nodes.values())
        total_demand = sum(node.demand for node in self.nodes.values())
        if total_generation == 0:
            raise ValueError("The grid must contain at least one generator.")
        if total_demand == 0:
            return

        if total_generation >= total_demand:
            # Trim excess generation proportionally.
            scale = total_demand / total_generation
            for node in self.nodes.values():
                if node.generation > 0:
                    node.generation *= scale
        else:
            # Shed load proportionally so the remaining demand can be met.
            scale = total_generation / total_demand
            for node in self.nodes.values():
                if node.demand > 0:
                    node.demand *= scale

    def _shortest_path(self, start: str, end: str, available_lines: Set[str]) -> Optional[List[str]]:
        """Breadth-first search to find any available path between two nodes."""

        queue: deque[str] = deque([start])
        visited: Set[str] = {start}
        parent: Dict[str, Optional[str]] = {start: None}

        while queue:
            current = queue.popleft()
            if current == end:
                break
            for neighbor in self.adj.get(current, []):
                line_id = self._line_between(current, neighbor)
                if line_id not in available_lines:
                    continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        if end not in parent:
            return None

        # Reconstruct path of nodes.
        path: List[str] = []
        node = end
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
        return path

    def _line_between(self, a: str, b: str) -> str:
        """
        Docstring for _line_between.
        """
        for line_id, line in self.lines.items():
            if not line.online:
                continue
            if {line.a, line.b} == {a, b}:
                return line_id
        raise KeyError(f"No line between {a} and {b}")

    def _route_power(self, available_lines: Set[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Docstring for _route_power.
        """
        flows: Dict[str, float] = {line_id: 0.0 for line_id in available_lines}
        generators = [node for node in self.nodes.values() if node.generation > 0]
        consumers = [node for node in self.nodes.values() if node.demand > 0]

        generator_surplus: Dict[str, float] = {g.name: g.surplus() for g in generators}
        consumer_deficit: Dict[str, float] = {c.name: c.deficit() for c in consumers}

        # Largest deficits first helps emphasize overloaded corridors.
        for consumer_name, deficit in sorted(consumer_deficit.items(), key=lambda x: x[1], reverse=True):
            while deficit > 1e-6:
                # Pick the closest generator with available surplus.
                candidate_paths: List[Tuple[int, float, str, List[str]]] = []
                for g_name, surplus in generator_surplus.items():
                    if surplus <= 1e-6:
                        continue
                    path = self._shortest_path(g_name, consumer_name, available_lines)
                    if path is None:
                        continue
                    candidate_paths.append((len(path), -surplus, g_name, path))

                if not candidate_paths:
                    break

                _, neg_surplus, g_name, path = min(candidate_paths)
                surplus = -neg_surplus
                transfer = min(deficit, surplus)
                # Record flow on all traversed lines.
                for i in range(len(path) - 1):
                    line_id = self._line_between(path[i], path[i + 1])
                    flows[line_id] += transfer
                generator_surplus[g_name] -= transfer
                deficit -= transfer

            consumer_deficit[consumer_name] = deficit

        return flows, consumer_deficit

    def simulate(self, initial_failures: Optional[Set[str]] = None) -> FlowResult:
        """
        Docstring for simulate.
        """
        self._ensure_balance()
        available_lines: Set[str] = {lid for lid, line in self.lines.items() if line.online}
        if initial_failures:
            for line_id in initial_failures:
                if line_id in available_lines:
                    available_lines.remove(line_id)

        failed_lines: List[str] = []
        while True:
            flows, unmet = self._route_power(available_lines)
            overloaded = [line_id for line_id, flow in flows.items() if flow - 1e-6 > self.lines[line_id].capacity]
            if not overloaded:
                return FlowResult(flows=flows, unmet_demand=unmet, failed_lines=failed_lines)

            # Mark overloaded lines as failed and reroute.
            for line_id in overloaded:
                available_lines.discard(line_id)
                failed_lines.append(line_id)

    def describe_flows(self, result: FlowResult) -> str:
        """
        Docstring for describe_flows.
        """
        lines = ["Line flows:"]
        for line_id, flow in sorted(result.flows.items()):
            capacity = self.lines[line_id].capacity
            status = "OVERLOADED" if flow - 1e-6 > capacity else "OK"
            lines.append(f"  {line_id:15s} : {flow:6.1f} / {capacity:6.1f} ({status})")

        if result.failed_lines:
            lines.append("Failed lines (cascade): " + ", ".join(result.failed_lines))
        unmet_total = sum(result.unmet_demand.values())
        if unmet_total > 1e-6:
            lines.append("Unserved demand:")
            for consumer, deficit in result.unmet_demand.items():
                if deficit > 1e-6:
                    lines.append(f"  {consumer}: {deficit:.1f} MW shed")
        else:
            lines.append("All demand served.")
        return "\n".join(lines)


def build_demo_grid() -> PowerGrid:
    """
    Docstring for build_demo_grid.
    """
    grid = PowerGrid()
    # Generators
    grid.add_generator("G1", generation=80)
    grid.add_generator("G2", generation=60)

    # Consumers
    grid.add_consumer("C1", demand=25)
    grid.add_consumer("C2", demand=20)
    grid.add_consumer("C3", demand=25)
    grid.add_consumer("C4", demand=20)
    grid.add_consumer("C5", demand=30)

    # Junction buses
    for hub in ("H1", "H2", "H3"):
        grid.add_consumer(hub, demand=0)  # demand 0 acts as a neutral bus

    # Transmission lines (MW capacities)
    grid.add_line("G1", "H1", capacity=90, name="G1-H1")
    grid.add_line("G2", "H2", capacity=90, name="G2-H2")
    grid.add_line("H1", "H2", capacity=70, name="Main Tie")
    grid.add_line("H1", "H3", capacity=35, name="North Spur")
    grid.add_line("H2", "H3", capacity=25, name="East Spur")

    # Feed consumers from hubs
    grid.add_line("H1", "C1", capacity=30, name="H1-C1")
    grid.add_line("H1", "C2", capacity=30, name="H1-C2")
    grid.add_line("H2", "C3", capacity=30, name="H2-C3")
    grid.add_line("H2", "C4", capacity=30, name="H2-C4")
    grid.add_line("H3", "C5", capacity=30, name="H3-C5")
    return grid


def run_demo() -> None:
    """
    Docstring for run_demo.
    """
    grid = build_demo_grid()
    print("=== Healthy grid ===")
    healthy = grid.simulate()
    print(grid.describe_flows(healthy))

    print("\n=== Trigger failure of Main Tie (expected cascade) ===")
    with_failure = grid.simulate(initial_failures={"Main Tie"})
    print(grid.describe_flows(with_failure))


if __name__ == "__main__":
    run_demo()
