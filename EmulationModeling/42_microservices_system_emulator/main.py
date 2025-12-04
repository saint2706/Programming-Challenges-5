import random
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx
import simpy
from simulation_core.discrete_event import DiscreteEventSimulation
from simulation_core.visualization import SimulationVisualizer

from .models import MicroserviceConfig


class Service:
    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        config: MicroserviceConfig,
        dependencies: List[str],
    ):
        self.env = env
        self.name = name
        self.config = config
        self.dependencies = dependencies
        self.queue = simpy.Resource(env, capacity=10)  # Limited concurrency
        self.stats = {"requests": 0, "failures": 0, "latency": []}

    def handle_request(self, req_id: int):
        self.stats["requests"] += 1
        start_time = self.env.now

        with self.queue.request() as req:
            yield req  # Wait for thread/resource

            # Simulate processing time (cold start or normal)
            latency = random.expovariate(1.0 / self.config.mean_latency)
            yield self.env.timeout(latency)

            # Call dependencies
            for dep_name in self.dependencies:
                # In a real sim we'd call the other service instance.
                # Here we simulate the delay and potential failure of calling a dependency
                yield self.env.timeout(0.01)  # Network hop

            # Simulate failure
            if random.random() < self.config.failure_rate:
                self.stats["failures"] += 1
                raise Exception("Service Failure")

        end_time = self.env.now
        self.stats["latency"].append(end_time - start_time)


class MicroserviceSimulation(DiscreteEventSimulation):
    def __init__(self, config: MicroserviceConfig):
        super().__init__(config.seed)
        self.config = config
        self.services: Dict[str, Service] = {}
        self.graph = nx.DiGraph()
        self.visualizer = SimulationVisualizer(
            output_dir=f"EmulationModeling/42_microservices_system_emulator/{config.output_dir}"
        )
        self.setup_system()

    def setup_system(self):
        # Create Services DAG
        # Gateway -> Auth, Gateway -> Product
        # Product -> DB, Product -> Inventory
        # Inventory -> DB

        adj = {
            "Gateway": ["Auth", "Product"],
            "Auth": [],
            "Product": ["DB", "Inventory"],
            "Inventory": ["DB"],
            "DB": [],
        }

        for name, deps in adj.items():
            self.services[name] = Service(self.env, name, self.config, deps)
            self.graph.add_node(name)
            for dep in deps:
                self.graph.add_edge(name, dep)

        self.schedule_process(self.request_generator)

    def request_generator(self):
        req_id = 0
        while True:
            yield self.env.timeout(random.expovariate(self.config.request_rate))
            req_id += 1
            self.schedule_process(self.trace_request, req_id)

    def trace_request(self, req_id):
        # Requests start at Gateway
        try:
            yield from self.services["Gateway"].handle_request(req_id)
        except:
            pass  # Request failed

        if req_id % 20 == 0:
            self.snapshot()

    def snapshot(self):
        fig, ax = plt.subplots(figsize=(8, 6))

        # Color nodes by failure rate or load
        colors = []
        for node in self.graph.nodes():
            svc = self.services[node]
            fail_rate = svc.stats["failures"] / max(1, svc.stats["requests"])
            # Map fail rate to color (Green -> Red)
            colors.append((fail_rate * 5, 1 - fail_rate * 5, 0))  # simplified

        pos = nx.shell_layout(self.graph)
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color="lightblue",
            node_size=2000,
            font_weight="bold",
            arrows=True,
            ax=ax,
        )

        # Overlay stats
        for node, (x, y) in pos.items():
            svc = self.services[node]
            ax.text(
                x,
                y - 0.1,
                f"Req: {svc.stats['requests']}\nFail: {svc.stats['failures']}",
                bbox=dict(facecolor="white", alpha=0.5),
                ha="center",
            )

        ax.set_title(f"Microservices Tracing (t={self.env.now:.1f})")
        self.visualizer.add_frame(fig)
        plt.close(fig)


def run_simulation():
    config = MicroserviceConfig(duration=50)
    sim = MicroserviceSimulation(config)
    sim.run(until=config.duration)
    sim.visualizer.save_gif("microservices_trace.gif")


if __name__ == "__main__":
    run_simulation()
