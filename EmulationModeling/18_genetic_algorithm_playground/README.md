# Genetic Algorithm Playground

This module provides reusable building blocks for simple genetic algorithm experiments, plus a demo that maximizes a multimodal function on the interval `[0, 1]`.

## Contents
- `ga_framework.py`: Core components for population initialization, fitness evaluation, roulette-wheel selection, one-point crossover, and mutation.
- `demo.py`: Example usage that logs the best and average fitness values each generation and saves a convergence plot (`fitness_convergence.png`).

## Running the demo

```bash
python EmulationModeling/18_genetic_algorithm_playground/demo.py
```

The script prints generation statistics and writes the convergence chart next to the script file.
