# Multidimensional Index (R-Tree)

## Theory
An **R-Tree** is a tree data structure used for spatial access methods, i.e., for indexing multi-dimensional information such as geographical coordinates, rectangles, or polygons.

1.  **Structure:** Similar to a B-Tree, but for spatial data. Nodes store **Minimum Bounding Rectangles (MBRs)** of their children.
2.  **Insertion:**
    *   Find the best leaf node to insert the new entry (one that requires minimal enlargement of its MBR).
    *   If the node is full, **split** it (e.g., using Linear or Quadratic split heuristic) and propagate the split upwards.
3.  **Search:** To find objects intersecting a query rectangle, start at root. Recursively visit subtrees whose MBRs intersect the query.

## Installation
No external dependencies.

## Usage
```bash
python main.py
```
This demo inserts cities into an R-Tree, saves it to `cities.json`, and performs spatial queries.

## Complexity Analysis
*   **Search:** $O(\log_M N)$ on average, but worst case can be $O(N)$ (if overlap is high). $M$ is max entries per node.
*   **Insert:** $O(\log_M N)$.
*   **Space:** $O(N)$.

## Demos
Run `main.py` to see spatial queries in action.
