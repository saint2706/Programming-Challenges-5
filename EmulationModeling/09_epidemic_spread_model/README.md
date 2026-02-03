# Epidemic Spread Model

An agent-based SIR (Susceptible-Infected-Recovered) model for simulating disease spread in a bounded 2D space.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Parameters](#parameters)

## 🧠 Theory

### Model Overview

Each individual is an **agent** with:
- A 2D position and velocity.
- A health state: **S**, **I**, or **R**.
- An infection timer that counts down to recovery.

The simulation advances in discrete steps:
1. **Movement:** Every agent updates position and bounces off walls.
2. **Recovery:** Infected agents decrement their timers and become recovered at zero.
3. **Transmission:** Infected agents attempt to infect nearby susceptible agents within a given radius, using a probability check.

### Ideal Example Test Case (Exercises Edge Cases)

Use a tiny, deterministic scenario that covers:
- **Immediate transmission**
- **No transmission due to distance**
- **Recovery at timer boundary**
- **Wall bounce behavior**

**Setup:**
- Bounds: width=10, height=10
- Infection radius = 2.0
- Infection probability = 1.0 (guaranteed transmission)
- Recovery time = 1 (recover in one step)
- Agents (positions, velocities):
  - A: infected, position (1, 1), velocity (1, 0)
  - B: susceptible, position (2, 1), velocity (0, 0)
  - C: susceptible, position (9, 9), velocity (1, 0) (will hit wall)

### Step-by-Step Walkthrough

#### Step 0 (Initial State)
- **A** is infected with timer=1.
- **B** is susceptible and within distance 1 of A (inside radius).
- **C** is far away, outside infection radius.

#### Step 1 (Movement)
1. A moves from (1,1) → (2,1).
2. B stays at (2,1).
3. C moves from (9,9) → (10,9), hits the wall, and bounces (velocity x flips).

#### Step 1 (Recovery)
- A's timer decreases from 1 to 0 → A transitions to **R**.

#### Step 1 (Transmission)
- A was infected during this step's transmission phase before recovery completes.
- Distance between A and B is 0 (same position), so B becomes **I** with timer=1.
- C remains **S** because it is far away.

#### Step 2 (Movement)
- A (now R) continues moving but no longer infects.
- B (now I) moves and may attempt to infect others.
- C continues after bounce with reversed x-velocity.

#### Step 2 (Recovery)
- B's timer hits 0 → B transitions to **R**.

**Outcome:**
- A and B become recovered, C remains susceptible. The example demonstrates infection, recovery boundary, distance-based non-infection, and wall bounce.

## 💻 Installation

Requires Python 3.8+ and NumPy:

```bash
pip install numpy
```

## 🚀 Usage

```bash
cd EmulationModeling/09_epidemic_spread_model
python main.py
```

## 📐 Parameters

### Transmission Rate (β)

Probability of disease transmission upon contact:
- Higher β → Faster spread
- Typical range: 0.1 - 0.5

### Recovery Time

Number of steps until an infected agent recovers.

### Contact Distance

Radius within which transmission can occur.

### Population Parameters

- **N**: Total population size
- **I₀**: Initial infected count
- **Mobility**: Agent movement speed

## 📊 Metrics

The simulation tracks over time:
- **S(t)**: Number of susceptible
- **I(t)**: Number of infected
- **R(t)**: Number of recovered
