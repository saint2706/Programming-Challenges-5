import math
import random

import networkx as nx
from simulation_core.discrete_event import DiscreteEventSimulation

from .models import LogisticsConfig


class LogisticsSimulation(DiscreteEventSimulation):
    def __init__(self, config: LogisticsConfig):
        super().__init__(config.seed)
        self.config = config
        self.graph = nx.Graph()
        self.depots = []
        self.customers = []
        self.trucks = []
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



def run_simulation():
    config = LogisticsConfig()
    sim = LogisticsSimulation(config)
    sim.run(until=config.duration)


if __name__ == "__main__":
    run_simulation()
