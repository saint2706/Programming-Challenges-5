# Cellular Automata Lab

A configurable cellular automata simulator with visualization support, implementing Conway's Game of Life and other Life-like rules.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)

## 🧠 Theory

### Cellular Automata
Cellular automata are discrete models where a grid of cells evolves over time based on simple rules:
- Each cell has a state (alive or dead)
- The next state depends on the current state and neighboring cells
- Rules are typically written in B/S notation: B (birth) and S (survival)

### Conway's Game of Life (B3/S23)
- **Birth**: A dead cell with exactly 3 live neighbors becomes alive
- **Survival**: A live cell with 2 or 3 live neighbors stays alive
- **Death**: All other cells die or stay dead

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:
```bash
pip install pygame numpy
```

## 🚀 Usage

### Running the Simulation
```bash
cd EmulationModeling/01_cellular_automata_lab
python main.py
```

### Custom Parameters
Configure grid size and cell display size:
```bash
python main.py --width 100 --height 80 --cell_size 8
```

### Controls
- **Space**: Pause/Resume simulation
- **R**: Randomize grid
- **C**: Clear grid
- **Mouse Click**: Toggle individual cells

## ✨ Features

- Real-time visualization with pygame
- Configurable grid dimensions
- Support for custom Life-like rules (B/S notation)
- Interactive cell editing
- Random initialization with adjustable density
