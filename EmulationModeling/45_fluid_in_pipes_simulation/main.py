import networkx as nx
import numpy as np
from scipy.integrate import odeint

from .models import PipeConfig


class PipeSimulation:
    def __init__(self, config: PipeConfig):
        self.config = config
        self.graph = nx.Graph()
        self.state = None  # Pressures at nodes
        self.setup_network()

    def setup_network(self):
        # Create a simple pipe network
        # 0 (Source) -> 1 -> 2 -> 3 (Sink)
        #               |    ^
        #               v    |
        #               4 -> 5

        edges = [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (5, 2)]
        for u, v in edges:
            self.graph.add_edge(u, v, resistance=1.0)

        self.pos = nx.spring_layout(self.graph, seed=42)

        # Initial pressures
        self.num_nodes = 6
        self.state = np.zeros(self.num_nodes)
        self.state[0] = 100.0  # Source pressure high
        self.state[3] = 0.0  # Sink pressure low

    def derivative(self, P, t):
        # dP/dt = sum(flow_in) - sum(flow_out)
        # Flow Q = (P_u - P_v) / R
        # This is actually a DAE if we assume incompressible, but let's model compressibility slightly
        # dP_i/dt = k * net_flow_i

        if P.ndim == 0 or P.shape == ():
            # Should not happen if y0 is array
            print(f"DEBUG: P is scalar? {P}")
            return 0.0

        dPdt = np.zeros_like(P)
        k = 10.0  # Bulk modulus / capacitance factor

        for u, v, data in self.graph.edges(data=True):
            R = data["resistance"]
            # P might be passed as scalar if shape mismatch occurs, but here we expect array.
            # However, if odeint passes a list or scalar for single eq, it's an issue.
            # But we have size 6.

            p_u = P[u]
            p_v = P[v]
            flow = (p_u - p_v) / R

            # Update pressures (Source and Sink are fixed BCs)
            # Node 0 is source, Node 3 is sink
            if u != 0 and u != 3:
                dPdt[u] -= k * flow
            if v != 0 and v != 3:
                dPdt[v] += k * flow

        # Fix BC explicitly just in case
        dPdt[0] = 0
        dPdt[3] = 0
        return dPdt

    def run(self):
        t = np.linspace(0, self.config.duration, int(self.config.duration * 30))

        # Solve ODE
        print(
            f"DEBUG: Starting odeint. state shape={self.state.shape}, state={self.state}"
        )
        try:
            solution = odeint(self.derivative, self.state, t)
        except Exception as e:
            print(f"DEBUG: odeint failed with {e}")
            raise e

        final_pressures = solution[-1]
        pressure_summary = ", ".join(
            f"{idx}:{pressure:.2f}" for idx, pressure in enumerate(final_pressures)
        )
        print(
            "Final pressures:",
            pressure_summary,
        )


def run_simulation():
    config = PipeConfig(duration=5.0)
    sim = PipeSimulation(config)
    sim.run()


if __name__ == "__main__":
    run_simulation()
