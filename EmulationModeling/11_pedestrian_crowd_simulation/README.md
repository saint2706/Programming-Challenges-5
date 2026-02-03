# Pedestrian Crowd Simulation

An agent-based simulation of pedestrians moving toward destinations while avoiding congestion.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Parameters](#parameters)

## 🧠 Theory

### Model Overview

Each pedestrian is an agent with a position, destination, and preferred direction. At each step, the simulator:
1. Computes desired movement vectors toward each destination.
2. Applies a simple avoidance force to reduce overlap.
3. Updates positions within the bounded environment.

### Ideal Example Test Case (Exercises Edge Cases)

**Setup:**
- Map size: 10 × 10
- Agents: 3
- Destinations: 3
- Initial positions:
  - A at (1,1) → destination (9,9)
  - B at (1,2) → destination (9,8)
  - C at (9,1) → destination (1,9)

This example forces:
- **Parallel movement** (A and B start near each other)
- **Crossing paths** (C moves opposite direction)
- **Boundary behavior** (agents approach edges)

### Step-by-Step Walkthrough

1. **Initialization**
   - Each agent is assigned a destination and initial velocity pointing toward it.
   - The simulator stores positions and destinations as arrays for efficient updates.

2. **Movement Vector Computation**
   - For A and B, vectors are similar, pointing toward the upper-right corner.
   - For C, the vector points toward the upper-left corner.

3. **Avoidance Adjustment**
   - A and B are close; the avoidance component nudges them apart so they do not overlap.
   - C is far enough that it does not affect A or B initially.

4. **Position Update**
   - New positions are computed by adding the adjusted movement vectors.
   - Positions are clamped to remain inside the 10 × 10 bounds.

5. **Iterative Convergence**
   - As A and B near their destinations, their velocity magnitudes shrink.
   - C crosses the center and eventually reaches its destination without collision.

This single case exercises crowding, crossing trajectories, and boundary enforcement.

## 💻 Installation

Requires Python 3.8+:

```bash
pip install numpy
```

## 🚀 Usage

```bash
cd EmulationModeling/11_pedestrian_crowd_simulation
python main.py --agents 25 --steps 300
```

## 📐 Parameters

- **agents**: number of pedestrians
- **steps**: number of simulation steps
