import math
import random
from typing import List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import simpy
from simulation_core.discrete_event import DiscreteEventSimulation
from simulation_core.visualization import SimulationVisualizer

from .models import DroneConfig


class DroneSimulation(DiscreteEventSimulation):
    def __init__(self, config: DroneConfig):
        super().__init__(config.seed)
        self.config = config
        self.visualizer = SimulationVisualizer(
            output_dir=f"EmulationModeling/47_drones_delivery_simulator/{config.output_dir}"
        )
        self.grid = np.zeros((config.map_size, config.map_size))  # 0=Free, 1=Obstacle
        self.orders = []
        self.drones = []
        self.charging_stations = []
        self.graph = None  # For A*

        self.setup_world()
        self.setup_graph()
        self.setup_agents()

    def setup_world(self):
        # Add random obstacles
        for _ in range(50):
            x, y = random.randint(0, self.config.map_size - 1), random.randint(
                0, self.config.map_size - 1
            )
            self.grid[x, y] = 1

        # Orders
        for i in range(self.config.num_orders):
            start = self.random_free_pos()
            end = self.random_free_pos()
            self.orders.append(
                {"id": i, "start": start, "end": end, "status": "pending"}
            )

        # Stations
        for _ in range(3):
            self.charging_stations.append(self.random_free_pos())

    def random_free_pos(self):
        while True:
            x, y = random.randint(0, self.config.map_size - 1), random.randint(
                0, self.config.map_size - 1
            )
            if self.grid[x, y] == 0:
                return (x, y)

    def setup_graph(self):
        # Create grid graph for pathfinding
        self.graph = nx.grid_2d_graph(self.config.map_size, self.config.map_size)
        # Remove obstacle nodes
        for x in range(self.config.map_size):
            for y in range(self.config.map_size):
                if self.grid[x, y] == 1:
                    if (x, y) in self.graph:
                        self.graph.remove_node((x, y))

    def setup_agents(self):
        for i in range(self.config.num_drones):
            drone = {
                "id": i,
                "pos": self.charging_stations[0],
                "battery": self.config.battery_capacity,
                "state": "idle",  # idle, delivering, charging
                "path": [],
            }
            self.drones.append(drone)
            self.schedule_process(self.drone_process, drone)

    def get_path(self, start, end):
        try:
            return nx.astar_path(
                self.graph,
                start,
                end,
                heuristic=lambda u, v: math.hypot(u[0] - v[0], u[1] - v[1]),
            )
        except nx.NetworkXNoPath:
            return []

    def drone_process(self, drone):
        while True:
            if drone["state"] == "idle":
                # Find pending order
                pending = [o for o in self.orders if o["status"] == "pending"]
                if pending:
                    order = pending[0]
                    order["status"] = "assigned"
                    drone["state"] = "delivering"

                    # Plan: Pos -> Pickup -> Dropoff
                    path_to_pickup = self.get_path(drone["pos"], order["start"])
                    path_to_drop = self.get_path(order["start"], order["end"])

                    full_path = path_to_pickup + path_to_drop[1:]

                    # Execute Path
                    yield from self.move_drone(drone, full_path)

                    order["status"] = "delivered"
                    drone["state"] = "idle"
                else:
                    yield self.env.timeout(1.0)  # Wait

            # Check battery logic (simplified)
            if drone["battery"] < 20:
                # Go charge
                station = self.charging_stations[0]  # closest
                path = self.get_path(drone["pos"], station)
                drone["state"] = "going_to_charge"
                yield from self.move_drone(drone, path)
                drone["state"] = "charging"
                yield self.env.timeout(5.0)
                drone["battery"] = self.config.battery_capacity
                drone["state"] = "idle"

            if int(self.env.now) % 5 == 0:
                self.snapshot()

    def move_drone(self, drone, path):
        for next_pos in path:
            if drone["battery"] <= 0:
                break  # crash

            # Move
            dist = 1.0
            travel_time = dist / self.config.drone_speed
            yield self.env.timeout(travel_time)

            drone["pos"] = next_pos
            drone["battery"] -= 0.5 * dist

    def snapshot(self):
        fig, ax = plt.subplots(figsize=(6, 6))

        # Draw obstacles
        obs_x, obs_y = np.where(self.grid == 1)
        ax.scatter(obs_x, obs_y, c="black", marker="s", s=20)

        # Draw Orders
        for o in self.orders:
            if o["status"] == "pending":
                ax.scatter(o["start"][0], o["start"][1], c="green", marker="^")
                ax.scatter(o["end"][0], o["end"][1], c="red", marker="v")

        # Draw Drones
        for d in self.drones:
            ax.scatter(d["pos"][0], d["pos"][1], c="blue", s=50, label="Drone")

        ax.set_title(f"Drone Delivery (t={self.env.now:.1f})")
        ax.set_xlim(0, self.config.map_size)
        ax.set_ylim(0, self.config.map_size)

        self.visualizer.add_frame(fig)
        plt.close(fig)


def run_simulation():
    config = DroneConfig(duration=50)
    sim = DroneSimulation(config)
    sim.run(until=config.duration)
    sim.visualizer.save_gif("drones.gif")


if __name__ == "__main__":
    run_simulation()
