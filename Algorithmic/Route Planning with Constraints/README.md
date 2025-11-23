# Route Planning with Constraints

## Theory
This challenge implements a route planner (pathfinder) that supports constraints beyond simple shortest path.

1.  **Core Algorithm:** Dijkstra's Algorithm (or A*) is used to find the shortest path between two points.
2.  **Constraints:**
    *   **Forbidden Nodes/Edges:** These are conceptually removed from the graph during the search. The algorithm simply checks if a node/edge is in the "forbidden" set before relaxing it.
    *   **Must-Visit Waypoints:** To visit a sequence of points $(P_1, P_2, \dots, P_k)$, we break the problem into segments: $Start \to P_1$, $P_1 \to P_2$, ..., $P_k \to End$. The final path is the concatenation of these shortest path segments.
        *   This implementation assumes an *ordered* list of waypoints. If the order is flexible (Traveling Salesperson Problem variant), the complexity increases significantly (NP-Hard).

## Installation
No external dependencies are required.

## Usage
Run the demo:

```bash
python main.py
```

The demo creates a 3x3 grid graph and solves paths with various constraints.

## Complexity Analysis
*   **Dijkstra:** $O(E \log V)$ where $E$ is edges and $V$ is vertices.
*   **Constraints:**
    *   **Forbidden:** Adds $O(1)$ check per edge relaxation. Total remains $O(E \log V)$.
    *   **Must-Visit (k waypoints):** Runs Dijkstra $k+1$ times. Total $O(k \cdot E \log V)$.

## Demos
See `main.py` output for examples of avoiding nodes and visiting specific waypoints.
