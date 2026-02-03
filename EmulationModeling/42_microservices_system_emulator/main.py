import random
from typing import Dict, List

import networkx as nx
import simpy
from simulation_core.discrete_event import DiscreteEventSimulation

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
        except Exception:
            pass  # Request failed



def run_simulation():
    config = MicroserviceConfig(duration=50)
    sim = MicroserviceSimulation(config)
    sim.run(until=config.duration)
    for name, service in sim.services.items():
        failures = service.stats["failures"]
        requests = service.stats["requests"]
        avg_latency = (
            sum(service.stats["latency"]) / len(service.stats["latency"])
            if service.stats["latency"]
            else 0.0
        )
        print(
            f"{name}: requests={requests} failures={failures} avg_latency={avg_latency:.3f}"
        )


if __name__ == "__main__":
    run_simulation()
