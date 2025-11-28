# K-d Tree & Nearest Neighbors

A Python implementation of a **k-dimensional tree (k-d tree)**, a space-partitioning data structure for organizing points in a k-dimensional space. This project demonstrates efficient **Nearest Neighbor** search algorithms.

![K-d Tree Construction](kd_tree_viz.gif)

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Construction

A k-d tree is a binary tree that splits points by hyperplanes.

- At each level, a specific dimension (axis) is chosen, cycling through $x, y, z, \dots$ or chosen based on variance.
- The set of points is sorted by the chosen axis, and the **median** point becomes the node.
- Points "left" of the median go to the left child; points "right" go to the right child.

### Search (Nearest Neighbor)

Searching is done via **branch-and-bound**:

1.  Traverse down to the leaf node closest to the query point.
2.  Unwind the recursion (backtrack).
3.  Keep track of the "best distance" found so far.
4.  **Pruning**: If the bounding box of a sibling node is further away than the current best distance, that entire subtree can be ignored.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Basic Usage

```python
from kd_tree import build_kd_tree, nearest_neighbor, k_nearest_neighbors

# Define 2D points
points = [
    [2, 3],
    [5, 4],
    [9, 6],
    [4, 7],
    [8, 1],
    [7, 2]
]

# Build the tree
root = build_kd_tree(points)

# Find nearest neighbor to (9, 2)
# Returns: (point, distance)
nearest, dist = nearest_neighbor(root, [9, 2])
print(f"Nearest: {nearest}, Distance: {dist}")

# Find 3 nearest neighbors
knn = k_nearest_neighbors(root, [9, 2], k=3)
print(f"3-NN: {knn}")
```

## 📊 Complexity Analysis

| Operation       | Time Complexity (Average) | Time Complexity (Worst) | Space Complexity                     |
| :-------------- | :------------------------ | :---------------------- | :----------------------------------- |
| **Build**       | $O(N \log N)$             | $O(N \log N)$           | $O(N)$                               |
| **Search (NN)** | $O(\log N)$               | $O(N)$                  | $O(1)$ (recursion stack $O(\log N)$) |

_Note: Curse of dimensionality applies. For very high dimensions ($d > 20$), k-d trees degrade to $O(N)$, similar to brute force._

## 🎬 Demos

### Running Tests & Benchmarks

Run the included test script to verify correctness and compare performance against brute force search.

```bash
python test_kd_tree.py
```

### Generating the Animation

To visualize the partitioning process:

```bash
manim -pql visualize_kd_tree.py KDTreeConstruction
```
