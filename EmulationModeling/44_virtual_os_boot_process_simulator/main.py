import random
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx
import simpy
from simulation_core.discrete_event import DiscreteEventSimulation
from simulation_core.visualization import SimulationVisualizer

from .models import BootConfig


class BootStage:
    def __init__(self, name: str, duration: float, dependencies: List[str]):
        self.name = name
        self.duration = duration
        self.dependencies = dependencies
        self.status = "PENDING"  # PENDING, RUNNING, DONE
        self.start_time = None
        self.end_time = None
        self.event = None  # SimPy event


class BootSimulation(DiscreteEventSimulation):
    def __init__(self, config: BootConfig):
        super().__init__(config.seed)
        self.config = config
        self.stages: Dict[str, BootStage] = {}
        self.graph = nx.DiGraph()
        self.visualizer = SimulationVisualizer(
            output_dir=f"EmulationModeling/44_virtual_os_boot_process_simulator/{config.output_dir}"
        )
        self.setup_dag()

    def setup_dag(self):
        # Define stages
        defs = [
            ("BIOS", 1.0, []),
            ("Bootloader", 0.5, ["BIOS"]),
            ("KernelInit", 2.0, ["Bootloader"]),
            ("MountFS", 1.5, ["KernelInit"]),
            ("NetInit", 1.0, ["KernelInit"]),
            ("StartServices", 0.0, ["MountFS", "NetInit"]),  # Pseudo-node
            ("SSHD", 0.5, ["StartServices"]),
            ("HTTPD", 0.8, ["StartServices"]),
            ("LoginPrompt", 0.2, ["SSHD", "HTTPD"]),
        ]

        for name, dur, deps in defs:
            stage = BootStage(name, dur, deps)
            stage.event = self.env.event()
            self.stages[name] = stage
            self.graph.add_node(name)
            for dep in deps:
                self.graph.add_edge(dep, name)

            self.schedule_process(self.run_stage, stage)

        self.schedule_process(self.monitor)

    def run_stage(self, stage: BootStage):
        # Wait for dependencies
        if stage.dependencies:
            yield simpy.AllOf(
                self.env, [self.stages[d].event for d in stage.dependencies]
            )

        # Start
        stage.status = "RUNNING"
        stage.start_time = self.env.now

        # Simulate work
        yield self.env.timeout(stage.duration)

        # Done
        stage.status = "DONE"
        stage.end_time = self.env.now
        stage.event.succeed()

    def monitor(self):
        while True:
            self.snapshot()
            if all(s.status == "DONE" for s in self.stages.values()):
                break
            yield self.env.timeout(0.2)
        self.snapshot()  # Final

    def snapshot(self):
        fig, ax = plt.subplots(figsize=(8, 6))

        pos = nx.spring_layout(self.graph, seed=42)  # Fixed layout

        colors = []
        for n in self.graph.nodes():
            s = self.stages[n]
            if s.status == "DONE":
                colors.append("green")
            elif s.status == "RUNNING":
                colors.append("orange")
            else:
                colors.append("gray")

        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color=colors,
            node_size=1500,
            font_weight="bold",
            ax=ax,
        )
        ax.set_title(f"Boot Process (t={self.env.now:.1f})")

        self.visualizer.add_frame(fig)
        plt.close(fig)


def run_simulation():
    config = BootConfig(duration=10)
    sim = BootSimulation(config)
    sim.run(until=config.duration)
    sim.visualizer.save_gif("boot_sequence.gif")


if __name__ == "__main__":
    run_simulation()
