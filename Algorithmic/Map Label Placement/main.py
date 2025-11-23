import matplotlib.pyplot as plt
import random
from label_placement import Label, MapLabeler

def main():
    random.seed(42)

    # Generate random points on a 100x100 map
    points = []
    labels = []

    map_size = 100
    num_points = 20

    for i in range(num_points):
        x = random.uniform(10, 90)
        y = random.uniform(10, 90)
        points.append((x, y))

        # Random label size
        w = random.uniform(10, 20)
        h = random.uniform(5, 8)

        lbl = Label(f"P{i+1}", x, y, w, h)
        labels.append(lbl)

    print("Running Simulated Annealing for Label Placement...")
    solver = MapLabeler(labels, (0, 0, map_size, map_size))

    initial_cost = solver.energy()
    print(f"Initial Energy: {initial_cost}")

    final_cost = solver.solve(iterations=50000)
    print(f"Final Energy: {final_cost}")

    # Visualization
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, map_size)
    ax.set_ylim(0, map_size)

    # Draw points
    for x, y in points:
        ax.plot(x, y, 'ko', markersize=3)

    # Draw labels
    for lbl in labels:
        x1, y1, x2, y2 = lbl.rect
        rect = plt.Rectangle((x1, y1), x2-x1, y2-y1,
                             fill=True, facecolor='lightblue', edgecolor='blue', alpha=0.5)
        ax.add_patch(rect)
        ax.text(x1 + (x2-x1)/2, y1 + (y2-y1)/2, lbl.text,
                ha='center', va='center', fontsize=8)

    plt.title(f"Map Label Placement (SA)\nInitial E: {initial_cost}, Final E: {final_cost}")
    plt.savefig("map_labels.png")
    print("Saved map_labels.png")

if __name__ == "__main__":
    main()
