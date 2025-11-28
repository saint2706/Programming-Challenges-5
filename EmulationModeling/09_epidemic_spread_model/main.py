from model import SIRModel


def main():
    print("Running SIR Model Headless...")
    model = SIRModel(num_agents=500, width=100, height=100)

    for i in range(500):
        model.step()
        if i % 50 == 0:
            stats = model.get_stats()
            print(f"Step {i}: S={stats['S']} I={stats['I']} R={stats['R']}")

            if stats["I"] == 0:
                print("Epidemic ended.")
                break

    stats = model.get_stats()
    print(f"Final: S={stats['S']} I={stats['I']} R={stats['R']}")
    print("\nRun 'python viz.py' for visualization.")


if __name__ == "__main__":
    main()
