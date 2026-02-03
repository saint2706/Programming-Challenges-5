import argparse

from simulation import CrowdSimulation

DEFAULT_STEPS = 300


def run_simulation(agent_count: int, steps: int) -> None:
    sim = CrowdSimulation(num_agents=agent_count, random_seed=42)

    for step in range(steps):
        sim.step()
        if step % 50 == 0:
            positions = sim.positions()
            sample = positions[0] if len(positions) else None
            print(f"Step {step}: sample_position={sample}")

    print(f"Completed {steps} simulation steps.")


def main():
    parser = argparse.ArgumentParser(
        description="Run the pedestrian crowd simulation in headless mode"
    )
    parser.add_argument(
        "--agents", type=int, default=25, help="Number of pedestrians to simulate"
    )
    parser.add_argument(
        "--steps", type=int, default=DEFAULT_STEPS, help="Number of simulation steps"
    )
    args = parser.parse_args()

    run_simulation(agent_count=args.agents, steps=args.steps)


if __name__ == "__main__":
    main()
