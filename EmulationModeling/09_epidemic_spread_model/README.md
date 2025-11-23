# Epidemic Spread Model

An agent-based SIR (Susceptible-Infected-Recovered) model for simulating disease spread with visualization.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Parameters](#parameters)

## 🧠 Theory

### SIR Model
A compartmental model dividing population into three states:
- **S (Susceptible)**: Can catch disease
- **I (Infected)**: Has disease, can spread it
- **R (Recovered)**: Had disease, now immune

### Disease Dynamics
```
S → I → R
```

Transitions occur based on:
1. **Contact**: Susceptible meets infected
2. **Transmission**: Disease spreads with probability p
3. **Recovery**: After fixed time, infected becomes recovered

### Agent-Based Modeling
Instead of differential equations, we simulate individual agents:
- Each person is an agent with position and state
- Agents move randomly in space
- Contact occurs when agents are close
- Stochastic transmission based on probability

## 💻 Installation

Requires Python 3.8+ with pygame and numpy:
```bash
pip install pygame numpy
```

## 🚀 Usage

### Running Simulation
```bash
cd EmulationModeling/09_epidemic_spread_model
python main.py
```

### With Visualization
```bash
python viz.py
```

Visualization shows:
- **Blue dots**: Susceptible individuals
- **Red dots**: Infected individuals
- **Green dots**: Recovered individuals

## 📐 Parameters

### Transmission Rate (β)
Probability of disease transmission upon contact:
- Higher β → Faster spread
- Typical range: 0.1 - 0.5

### Recovery Time
Days until infected person recovers:
- Affects peak infection time
- Typical range: 7-14 days

### Contact Distance
Radius within which transmission can occur:
- Smaller distance → Slower spread
- Models social distancing

### Population Parameters
- **N**: Total population size
- **I₀**: Initial infected count
- **Mobility**: Agent movement speed

## 📊 Metrics

The simulation tracks over time:
- **S(t)**: Number of susceptible
- **I(t)**: Number of infected
- **R(t)**: Number of recovered

### Epidemic Curve
Plot of infected over time shows:
- **Exponential Growth**: Early phase
- **Peak**: Maximum infected simultaneously
- **Decline**: As susceptible depleted

### R₀ (Basic Reproduction Number)
Average number of people one infected person infects:
- R₀ < 1: Epidemic dies out
- R₀ > 1: Epidemic spreads
- R₀ = β × contacts × recovery_time

## ✨ Features

- Agent-based SIR model
- Real-time visualization
- Configurable disease parameters
- Spatial movement simulation
- Time-series plots of compartments
- Support for intervention strategies (e.g., lockdown)
