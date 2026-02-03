# Robot Swarm Simulator

Agent-based system with 100–500 robots in a 2D plane exhibiting emergent behavior (Boids logic).

## 📋 Table of Contents

- [Theory](#theory)
- [How to Run](#how-to-run)

## 🧠 Theory

### Core Behaviors

Each robot updates its velocity based on three weighted influences:
1. **Alignment**: steer toward average neighbor velocity.
2. **Cohesion**: steer toward the neighbor center of mass.
3. **Separation**: steer away to avoid crowding.

A spatial index (KDTree) is used to find neighbors efficiently.

### Ideal Example Test Case (Exercises Edge Cases)

**Setup:**
- 3 robots on a 10 × 10 plane
- Perception radius = 3
- Max speed = 2
- Robots:
  - R1 at (2, 2) with velocity (1, 0)
  - R2 at (3, 2) with velocity (1, 0)
  - R3 at (9, 9) with velocity (-1, 0)

This case triggers:
- **Alignment and cohesion** between R1 and R2.
- **No neighbor influence** for distant R3.
- **Toroidal wrap** if a robot exits the boundary.

### Step-by-Step Walkthrough

1. **Neighbor search**
   - R1 and R2 see each other (distance 1).
   - R3 has no neighbors within radius.

2. **Alignment**
   - R1 and R2 already share velocity (1,0), so alignment force is near zero.

3. **Cohesion**
   - R1 moves slightly toward R2’s position (3,2).
   - R2 moves slightly toward R1’s position (2,2).

4. **Separation**
   - R1 and R2 push away from each other to avoid overlap.

5. **Velocity update and speed limit**
   - Combined forces adjust velocities; any magnitude above max speed is scaled down.

6. **Position update and wrapping**
   - Positions update by velocity * dt.
   - If a robot crosses an edge, it wraps around to the opposite side.

This example demonstrates coupling between nearby agents and isolation for distant agents.

## ▶️ How to Run

```bash
python EmulationModeling/46_robot_swarm_simulator/main.py
```
