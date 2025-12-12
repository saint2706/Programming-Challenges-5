# Drones Delivery Simulator

Graph-based delivery network with drone fleet, battery management, and obstacles.

## How to Run

```bash
python EmulationModeling/47_drones_delivery_simulator/main.py
```

## Logic

1.  **Environment**: Grid with obstacles (no-fly zones). Modeled as a graph for pathfinding.
2.  **Pathfinding**: A\* algorithm (`networkx.astar_path`) used to route drones around obstacles.
3.  **Agents**: Drones pick up packages from Start -> End.
4.  **Battery**: Drones consume battery while moving. (Simplified logic: go to charge if low).
5.  **Visualization**: Scatter plot showing obstacles (black), packages (green/red), and drones (blue).
