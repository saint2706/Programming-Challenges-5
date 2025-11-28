# Elevator System Model

A discrete event simulator for multi-elevator systems with different scheduling algorithms.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Scheduling Algorithms](#scheduling-algorithms)

## 🧠 Theory

### Elevator System Components

- **Elevators**: Move between floors, carry passengers
- **Requests**: Floor calls (up/down) and destination requests
- **Scheduler**: Assigns requests to elevators
- **State Machine**: Each elevator tracks position, direction, doors

### Discrete Event Simulation

The system operates on discrete events:

- **Request Arrival**: Passenger presses button
- **Elevator Arrival**: Elevator reaches floor
- **Door Operations**: Opening/closing cycles
- **Travel**: Movement between floors

## 💻 Installation

Requires Python 3.8+ (no external dependencies):

```bash
cd EmulationModeling/06_elevator_system_model
python main.py
```

## 🚀 Usage

### Running Simulation

```bash
python main.py
```

The simulation demonstrates different scheduling algorithms with sample request patterns.

## 🎯 Scheduling Algorithms

### FCFS (First-Come-First-Served)

- Simplest algorithm
- Serves requests in arrival order
- May cause poor performance with many requests

### SCAN (Elevator Algorithm)

- Elevator continues in current direction
- Serves all requests in that direction
- Reverses when no more requests ahead
- Similar to disk scheduling

### LOOK

- Variation of SCAN
- Only goes as far as last request
- Doesn't travel to building extremes unnecessarily

### Nearest-Car

- Assigns request to closest available elevator
- Considers both distance and direction
- Minimizes average wait time

## 📊 Performance Metrics

The simulation tracks:

- **Average Wait Time**: Time from request to pickup
- **Average Travel Time**: Time from pickup to destination
- **Elevator Utilization**: Percentage of time carrying passengers
- **Energy Efficiency**: Total distance traveled

## ✨ Features

- Multiple scheduling algorithms
- Configurable number of elevators and floors
- Request generation with realistic patterns
- Performance comparison between algorithms
- Support for up/down call buttons
