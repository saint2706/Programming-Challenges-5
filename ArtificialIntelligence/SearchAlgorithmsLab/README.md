# Search Algorithms Lab

## Overview
This project implements fundamental search algorithms used in Artificial Intelligence: Breadth-First Search (BFS), Depth-First Search (DFS), and A* Search. It demonstrates pathfinding on a grid or graph structure.

## Features
- **BFS:** Explores all neighbors at the present depth prior to moving on to nodes at the next depth level. Guarantees shortest path in unweighted graphs.
- **DFS:** Explores as far as possible along each branch before backtracking.
- **A* Search:** Uses a heuristic function to estimate the cost to reach the goal, prioritizing promising paths.

## Installation
1.  Navigate to the project directory:
    ```bash
    cd ArtificialIntelligence/SearchAlgorithmsLab
    ```
2.  Install dependencies (if any):
    ```bash
    # No external dependencies required
    ```

## Usage
Run the script to see the algorithms in action:
```bash
python search_algorithms.py
```

## Implementation Details
- Uses `collections.deque` for the queue in BFS.
- Uses recursion or a stack for DFS.
- Uses `heapq` for the priority queue in A*.

## Future Improvements
- Visualize the search process using a GUI library.
- Allow user to define custom graphs/grids.
