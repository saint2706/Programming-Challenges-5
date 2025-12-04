import math
import random
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import simpy
from simulation_core.discrete_event import DiscreteEventSimulation
from simulation_core.visualization import SimulationVisualizer

from .models import LogisticsConfig


class LogisticsSimulation(DiscreteEventSimulation):
    def __init__(self, config: LogisticsConfig):
        super().__init__(config.seed)
        self.config = config
        self.graph = nx.Graph()
        self.depots = []
        self.customers = []
        self.trucks = []
        self.visualizer = SimulationVisualizer(
            output_dir=f"EmulationModeling/40_logistics_routing_simulator/{config.output_dir}"
        )
        self.setup_world()

    def setup_world(self):
        # Create Depots
        for i in range(self.config.num_depots):
            pos = (
                random.randint(0, self.config.map_size),
                random.randint(0, self.config.map_size),
            )
            self.depots.append({"id": f"D{i}", "pos": pos})
            self.graph.add_node(f"D{i}", pos=pos, type="depot")

        # Create Customers
        for i in range(self.config.num_customers):
            pos = (
                random.randint(0, self.config.map_size),
                random.randint(0, self.config.map_size),
            )
            demand = random.randint(10, 50)
            self.customers.append(
                {"id": f"C{i}", "pos": pos, "demand": demand, "served": False}
            )
            self.graph.add_node(f"C{i}", pos=pos, type="customer", demand=demand)

        # Connect everything fully connected (simplification) with Euclidean distances
        nodes = self.depots + self.customers
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                dist = math.hypot(u["pos"][0] - v["pos"][0], u["pos"][1] - v["pos"][1])
                self.graph.add_edge(u["id"], v["id"], weight=dist)

        # Create Trucks
        for i in range(self.config.num_trucks):
            # Start at random depot
            start_depot = random.choice(self.depots)
            self.trucks.append(
                {
                    "id": f"T{i}",
                    "pos": start_depot["pos"],
                    "target": None,
                    "load": 0,
                    "capacity": self.config.truck_capacity,
                    "path": [start_depot["id"]],
                }
            )
            self.schedule_process(self.truck_process, i)

    def truck_process(self, truck_idx):
        truck = self.trucks[truck_idx]
        speed = 50  # units per tick

        while True:
            # Simple Logic: Find nearest unserved customer with demand <= remaining capacity
            # If none, go back to nearest depot to reload

            # Find current node
            current_node_id = truck["path"][-1]
            current_pos = self.graph.nodes[current_node_id]["pos"]

            potential_customers = [
                c
                for c in self.customers
                if not c["served"] and c["demand"] + truck["load"] <= truck["capacity"]
            ]

            target = None
            if potential_customers:
                # Find nearest
                potential_customers.sort(
                    key=lambda c: math.hypot(
                        c["pos"][0] - current_pos[0], c["pos"][1] - current_pos[1]
                    )
                )
                target = potential_customers[0]
                action = "deliver"
            else:
                # Go to depot if has load or if empty but no customers fit (Wait/Refill)
                # Actually if empty and no customers fit, we are done or need to wait.
                # Simplification: Go to nearest depot
                depots_sorted = sorted(
                    self.depots,
                    key=lambda d: math.hypot(
                        d["pos"][0] - current_pos[0], d["pos"][1] - current_pos[1]
                    ),
                )
                target = depots_sorted[0]
                action = "refill"

            # Move to target
            dist = math.hypot(
                target["pos"][0] - current_pos[0], target["pos"][1] - current_pos[1]
            )
            travel_time = dist / speed
            yield self.env.timeout(travel_time)

            # Arrive
            truck["pos"] = target["pos"]
            truck["path"].append(target["id"])

            if action == "deliver":
                truck["load"] += target["demand"]
                target["served"] = True
                # print(f"Truck {truck['id']} served {target['id']} at {self.env.now:.2f}")
            elif action == "refill":
                truck["load"] = 0
                yield self.env.timeout(5)  # loading time

            # Visualization step (snapshot)
            if int(self.env.now) % 10 == 0:
                self.snapshot()

    def snapshot(self):
        fig, ax = plt.subplots(figsize=(8, 8))
        pos = nx.get_node_attributes(self.graph, "pos")

        # Draw edges
        # nx.draw_networkx_edges(self.graph, pos, alpha=0.1, ax=ax)

        # Draw Depots
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            nodelist=[d["id"] for d in self.depots],
            node_color="red",
            node_size=100,
            label="Depot",
            ax=ax,
        )

        # Draw Customers (served vs unserved)
        unserved = [c["id"] for c in self.customers if not c["served"]]
        served = [c["id"] for c in self.customers if c["served"]]
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            nodelist=unserved,
            node_color="blue",
            node_size=50,
            label="Customer (Wait)",
            ax=ax,
        )
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            nodelist=served,
            node_color="green",
            node_size=50,
            label="Customer (Done)",
            ax=ax,
        )

        # Draw Trucks
        truck_pos = {t["id"]: t["pos"] for t in self.trucks}
        # Since trucks might be between nodes, we use their stored pos
        # But nx.draw expects node IDs. We'll just scatter plot them.
        tx = [t["pos"][0] for t in self.trucks]
        ty = [t["pos"][1] for t in self.trucks]
        ax.scatter(tx, ty, c="orange", s=80, marker="s", label="Truck")

        ax.legend()
        ax.set_title(f"Logistics Simulation (t={self.env.now:.1f})")
        self.visualizer.add_frame(fig)
        plt.close(fig)


def run_simulation():
    config = LogisticsConfig()
    sim = LogisticsSimulation(config)
    sim.run(until=config.duration)
    sim.visualizer.save_gif("simulation.gif", fps=10)


if __name__ == "__main__":
    run_simulation()
