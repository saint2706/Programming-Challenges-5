from simulation import run_simulation


def main():
    print("Running headless simulation...")
    stats = run_simulation(duration=1000)
    print("Simulation Complete.")
    print(f"Total Cars Arrived: {stats['arrived']}")
    print(f"Total Cars Crossed: {stats['crossed']}")
    if stats["crossed"] > 0:
        avg_wait = stats["total_wait_time"] / stats["crossed"]
        print(f"Average Wait Time: {avg_wait:.2f}s")
    else:
        print("No cars crossed.")

    print("\nTo run visualizer, execute: python viz.py")


if __name__ == "__main__":
    main()
