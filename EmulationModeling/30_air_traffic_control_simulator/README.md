# Air Traffic Control Simulator

A simulation of aircraft movement and conflict detection in 3D space.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Conflict Detection

The simulator predicts potential conflicts between aircraft pairs.
A conflict occurs if two aircraft violate minimum separation standards:

- **Lateral Separation**: Minimum horizontal distance (e.g., 5 km).
- **Vertical Separation**: Minimum vertical distance (e.g., 0.3 km).

The prediction uses relative velocity vectors to solve a quadratic equation for the time of closest approach ($t_{min}$).

$$d^2(t) = |\vec{p}(t)|^2 = |\vec{p}_0 + \vec{v}t|^2$$

We find $t$ where $d(t) < \text{separation}$.

## 💻 Installation

Ensure you have a C++17 compatible compiler (e.g., `g++`, `clang++`).

## 🚀 Usage

### Compiling and Running

The project is a single-file C++ implementation.

```bash
g++ -std=c++17 -DATC_SIM_DEMO main.cpp -o atc_sim
./atc_sim
```

### API

```cpp
AirTrafficSimulator sim(5.0, 0.3, 45.0); // Lateral 5km, Vert 0.3km, Lookahead 45min
sim.add_aircraft({"A1", 0, 0, 10, 12, 0, 0});
auto conflicts = sim.detect_conflicts();
```

## 📊 Complexity Analysis

| Operation            | Complexity | Description                      |
| :------------------- | :--------- | :------------------------------- |
| **Detect Conflicts** | $O(N^2)$   | Pairwise check of all aircraft.  |
| **Step Simulation**  | $O(N)$     | Update position of all aircraft. |

_Where $N$ is the number of aircraft._

## 🎬 Demos

Running the compiled executable produces a list of detected conflicts:

```text
Conflict between A2 and A1 in 2.72727 minutes (miss: 0 km)
```
