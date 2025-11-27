# Solar System N-Body Simulation

A physics simulation of the gravitational interaction between multiple celestial bodies.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Newton's Law of Universal Gravitation
The force between two bodies $i$ and $j$ is:
$$\vec{F}_{ij} = G \frac{m_i m_j}{|\vec{r}|^2} \hat{r}$$

### Numerical Integration
We use the **Symplectic Euler** or **Velocity Verlet** method to update positions and velocities over discrete time steps $\Delta t$.
$$v_{t+1} = v_t + \frac{F}{m} \Delta t$$
$$x_{t+1} = x_t + v_{t+1} \Delta t$$

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DNBODY_DEMO main.cpp -o n_body
./n_body
```

### API
```cpp
NBodySim sim;
sim.add_body({mass, x, y, vx, vy});
sim.step(dt);
```

## 📊 Complexity Analysis

-   **Force Calculation**: $O(N^2)$ per step (computing pairwise forces).
-   **Integration**: $O(N)$ per step.
-   **Total**: $O(T \cdot N^2)$ where $T$ is number of steps.

*(Note: Barnes-Hut algorithm can reduce this to $O(N \log N)$ but is not implemented here.)*

## 🎬 Demos

The demo simulates a Sun-Earth-Moon system and prints their coordinates over time.
