# Drones Delivery Simulator

Graph-based delivery network with drone fleet, battery management, and obstacles.

## 📋 Table of Contents

- [Theory](#theory)
- [How to Run](#how-to-run)

## 🧠 Theory

### Core Components

1. **Environment**: Grid with obstacles (no-fly zones). Modeled as a graph for pathfinding.
2. **Pathfinding**: A* search (`networkx.astar_path`) routes drones around obstacles.
3. **Agents**: Drones move from pickup to drop-off points.
4. **Battery**: Each move drains battery; drones must recharge at stations.

### Ideal Example Test Case (Exercises Edge Cases)

**Setup:**
- Grid size: 5 × 5
- Obstacles at (2,2) and (2,3)
- One drone at (0,0) with battery=3
- One order: start (0,1) → end (4,4)
- One charging station at (0,0)

This case exercises:
- **Obstacle detour** (A* must route around (2,2)/(2,3)).
- **Battery depletion** mid-route.
- **Recharge cycle** before completing the order.

### Step-by-Step Walkthrough

1. **Graph construction**
   - All grid cells become nodes except obstacle cells.
   - Edges connect adjacent free cells.

2. **Order assignment**
   - Drone at (0,0) is idle → assigned the pending order.

3. **Path planning to pickup**
   - A* finds shortest route from (0,0) to (0,1).

4. **Delivery route planning**
   - A* computes a path to (4,4) avoiding obstacles.

5. **Battery check**
   - Battery=3 cannot cover full route; drone switches to charging state.

6. **Recharge**
   - Drone returns to station (0,0), waits, battery resets.

7. **Delivery completion**
   - Drone resumes path, reaches (4,4), marks order delivered.

This example covers obstacle avoidance, re-planning, and battery management.

## ▶️ How to Run

```bash
python EmulationModeling/47_drones_delivery_simulator/main.py
```
