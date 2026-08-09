# Pedestrian Crowd Simulation

A simple 2D crowd simulator where each pedestrian moves toward a destination while repelling nearby agents to preserve personal space. The model illustrates how local interactions shape crowd flow.

## 🧠 Model Overview

- **Goal force:** Pulls each pedestrian toward their individual destination.
- **Repulsive force:** Pushes agents apart when they are within a personal-space radius.
- **Speed limiting:** Caps velocity to avoid unrealistic acceleration spikes.
- **Boundary clamping:** Keeps pedestrians inside the simulation area.

## 🚀 Running the Simulation

```bash
cd EmulationModeling/11_pedestrian_crowd_simulation
python main.py --agents 40 --steps 400
```

An interactive matplotlib window will display blue dots for pedestrians and red crosses for their destinations.

## 🧪 Testing

From the repository root:

```bash
python -m pytest tests/EmulationModeling/test_11_pedestrian_crowd_simulation.py
```

## 🛠️ Configuration

Key parameters live in `CrowdSimulation` (see `simulation.py`):

- `goal_strength`: Attraction intensity toward destinations.
- `personal_space_radius`: Distance at which repulsion activates.
- `repulsion_strength`: Strength of the push away from nearby agents.
- `max_speed`: Caps pedestrian velocity.
- `dt`: Time-step size.

Feel free to tweak these values or reset agent positions/destinations programmatically for experiments.
