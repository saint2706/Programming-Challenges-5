# Traffic Intersection Simulator

A discrete event simulation modeling traffic flow through a 4-way intersection with traffic light control.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Metrics](#metrics)

## 🧠 Theory

### Discrete Event Simulation
Models a system as a sequence of events occurring at discrete time points:
- **Events**: Car arrivals, light changes, cars crossing
- **Event Queue**: Priority queue ordered by event time
- **State**: Current light state, cars waiting at each direction

### Traffic Light Logic
- **Cycle**: Alternates between North-South (NS) and East-West (EW)
- **Green Time**: Configurable duration for each direction
- **Queue Processing**: Cars cross one at a time when light is green

### Performance Metrics
- **Average Wait Time**: Time from arrival to crossing
- **Throughput**: Number of cars crossing per time unit
- **Queue Length**: Cars waiting at each direction

## 💻 Installation

Requires Python 3.8+ and pygame for visualization:
```bash
pip install pygame
```

## 🚀 Usage

### Headless Simulation
Run simulation without visualization to collect statistics:
```bash
cd EmulationModeling/04_traffic_intersection_simulator
python main.py
```

Output:
```
Total Cars Arrived: 245
Total Cars Crossed: 238
Average Wait Time: 12.34s
```

### Visual Simulation
Run with real-time visualization:
```bash
python viz.py
```

## 📊 Metrics

The simulation tracks:
- **Cars Arrived**: Total cars entering the system
- **Cars Crossed**: Cars that successfully crossed
- **Total Wait Time**: Sum of all wait times
- **Average Wait Time**: Total wait / cars crossed

## ✨ Features

- Discrete event simulation engine
- Configurable arrival rates and light cycles
- Statistical analysis of traffic flow
- Optional real-time visualization
- Support for 4-way intersection
