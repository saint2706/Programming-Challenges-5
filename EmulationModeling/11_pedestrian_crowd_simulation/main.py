import argparse
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from simulation import CrowdSimulation


DEFAULT_STEPS = 300


def run_animation(agent_count: int, steps: int) -> None:
    sim = CrowdSimulation(num_agents=agent_count, random_seed=42)

    fig, ax = plt.subplots()
    ax.set_xlim(0, sim.width)
    ax.set_ylim(0, sim.height)
    ax.set_title("Pedestrian Crowd Simulation")
    ax.set_xlabel("X position")
    ax.set_ylabel("Y position")

    agents_plot = ax.scatter([], [], s=40, c="tab:blue", label="Pedestrians")
    destinations_plot = ax.scatter([], [], marker="x", c="tab:red", label="Destinations")
    ax.legend(loc="upper right")

    def init():
        agents_plot.set_offsets([])
        destinations_plot.set_offsets([])
        return agents_plot, destinations_plot

    def update(_frame):
        sim.step()
        agents_plot.set_offsets(sim.positions())
        destinations_plot.set_offsets(sim.destinations())
        return agents_plot, destinations_plot

    FuncAnimation(fig, update, init_func=init, frames=steps, interval=50, blit=True)
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize the pedestrian crowd simulation")
    parser.add_argument("--agents", type=int, default=25, help="Number of pedestrians to simulate")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Number of animation frames")
    args = parser.parse_args()

    run_animation(agent_count=args.agents, steps=args.steps)


if __name__ == "__main__":
    main()
