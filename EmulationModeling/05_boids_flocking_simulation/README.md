# Boids Flocking Simulation

An implementation of Craig Reynolds' Boids algorithm for simulating emergent flocking behavior in artificial life.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [The Three Rules](#the-three-rules)

## 🧠 Theory

### Boids Algorithm
Developed by Craig Reynolds in 1986, the Boids algorithm demonstrates how complex flocking behavior emerges from three simple local rules applied to each agent (boid).

### Emergent Behavior
- **Local Rules**: Each boid only considers nearby neighbors
- **Global Patterns**: Coordinated flock movement emerges naturally
- **No Leader**: Collective behavior without centralized control

## 💻 Installation

Requires Python 3.8+ with pygame and numpy:
```bash
pip install pygame numpy
```

## 🚀 Usage

### Running the Simulation
```bash
cd EmulationModeling/05_boids_flocking_simulation
python main.py
```

The simulation creates 50 boids that move according to flocking rules. Each boid is rendered as a small triangle pointing in its direction of travel.

## 📐 The Three Rules

### 1. Separation
**Avoid crowding**: Steer away from boids that are too close
- Prevents collision
- Creates personal space
- Weight: Higher priority for very close neighbors

### 2. Alignment
**Match velocity**: Steer towards the average heading of neighbors
- Coordinates direction
- Creates coherent movement
- Smooths transitions

### 3. Cohesion
**Move to center**: Steer towards the average position of neighbors
- Keeps flock together
- Prevents fragmentation
- Acts as long-range attraction

### Parameter Tuning
Each rule has an associated weight that controls its influence. Adjusting these weights produces different flocking behaviors:
- **High Separation**: Sparse, dispersed flocks
- **High Alignment**: Coordinated, stream-like movement
- **High Cohesion**: Tight, compact flocks

## ✨ Features

- Real-time visualization with pygame
- Configurable flock size
- Toroidal boundary conditions (wrap-around)
- Smooth animation at 60 FPS
- Triangle sprites aligned with velocity
