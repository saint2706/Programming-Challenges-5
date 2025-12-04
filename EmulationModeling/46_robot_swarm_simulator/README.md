# Robot Swarm Simulator

Agent-based system with 100–500 robots in a 2D plane exhibiting emergent behavior (Boids logic).

## How to Run

```bash
python EmulationModeling/46_robot_swarm_simulator/main.py
```

## Logic

1.  **State**: Each robot has position and velocity.
2.  **Neighbors**: Efficiently found using `scipy.spatial.KDTree`.
3.  **Behaviors**:
    *   **Alignment**: Match velocity of neighbors.
    *   **Cohesion**: Move towards center of neighbors.
    *   **Separation**: Avoid overcrowding.
4.  **Vectorization**: Updates are computed using NumPy arrays.
5.  **Visualization**: Quiver plot (arrows) showing position and direction.
