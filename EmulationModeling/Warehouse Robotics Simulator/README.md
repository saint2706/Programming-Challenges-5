# Warehouse Robotics Simulator

A pathfinding simulation for multi-agent robotics in a grid-based warehouse environment.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Pathfinding (A*)
Robots use the A* algorithm to find the shortest path from start to goal.
$$f(n) = g(n) + h(n)$$
-   $g(n)$: Cost from start to node $n$.
-   $h(n)$: Heuristic estimate (Manhattan distance) from $n$ to goal.

### Collision Avoidance
Basic reservation table or prioritized planning:
-   Robots reserve (x, y, time) slots.
-   If a robot tries to move to a cell reserved by another robot at that time, it waits or replans.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DWAREHOUSE_SIM_DEMO main.cpp -o warehouse
./warehouse
```

## 📊 Complexity Analysis

-   **A* Search**: $O(E)$ where $E$ is number of edges in the grid graph ($4 \cdot W \cdot H$).
-   **Multi-Agent**: Planning $R$ robots sequentially is $O(R \cdot (W \cdot H))$.

## 🎬 Demos

The demo sets up a grid with obstacles and calculates paths for robots, printing the grid state step-by-step.
