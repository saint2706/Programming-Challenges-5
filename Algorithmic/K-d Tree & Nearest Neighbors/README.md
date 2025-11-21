# K-d Tree & Nearest Neighbors

Median-split k-d tree with dimensionality-agnostic nearest-neighbor and k-NN search, plus brute-force baselines and simple benchmarks.

## Visualization
![K-d Tree Construction](kd_tree_viz.gif)

## Features
- Median splitting with alternating axes to keep the tree balanced.
- Bounds stored per node for branch-and-bound pruning.
- Priority-queue backtracking for nearest-neighbor and k-NN queries.
- Euclidean distance by default, but any distance function can be injected.
- Brute-force helpers and a benchmark harness to compare performance.

## Quickstart
```python
from pathlib import Path
import importlib.util

module_path = Path("Algorithmic/K-d Tree & Nearest Neighbors/kd_tree.py")
spec = importlib.util.spec_from_file_location("kd_tree", module_path)
kd_tree = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd_tree)

points = [[0.0, 1.0], [2.0, 3.5], [-1.0, 4.2]]
root = kd_tree.build_kd_tree(points)

print(kd_tree.nearest_neighbor(root, [1.5, 3.0]))
print(kd_tree.k_nearest_neighbors(root, [1.5, 3.0], k=2))
```

Run the benchmarks directly:
```bash
python "Algorithmic/K-d Tree & Nearest Neighbors/test_kd_tree.py"
```
