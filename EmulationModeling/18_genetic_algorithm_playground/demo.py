"""Demonstration of the genetic algorithm framework.

The demo optimizes a simple one-variable function and logs fitness
statistics per generation. A convergence plot is saved alongside the
script as ``fitness_convergence.png``.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import matplotlib.pyplot as plt
from ga_framework import GAConfig, GeneticAlgorithm

random.seed(42)


def target_function(x: float) -> float:
    """A multimodal function to maximize on the domain [0, 1]."""
    return x * math.sin(10 * math.pi * x) + 1.0


def genome_to_value(genome: list[float]) -> float:
    return genome[0]


def fitness_fn(genome: list[float]) -> float:
    return target_function(genome_to_value(genome))


def run_demo(generations: int = 60) -> list[dict[str, float]]:
    config = GAConfig(
        population_size=40,
        genome_length=1,
        bounds=[(0.0, 1.0)],
        crossover_rate=0.9,
        mutation_rate=0.15,
        mutation_scale=0.1,
    )
    ga = GeneticAlgorithm(config=config, fitness_fn=fitness_fn)
    history = ga.run(generations)

    for idx, metrics in enumerate(history, start=1):
        print(
            f"Generation {idx:02d}: best={metrics['best_fitness']:.5f} avg={metrics['avg_fitness']:.5f}"
        )
    return history


def plot_history(history: list[dict[str, float]]) -> Path:
    best = [entry["best_fitness"] for entry in history]
    avg = [entry["avg_fitness"] for entry in history]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(best, label="Best fitness", linewidth=2)
    ax.plot(avg, label="Average fitness", linestyle="--")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness")
    ax.set_title("Genetic Algorithm Convergence")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.7)

    output_path = Path(__file__).with_name("fitness_convergence.png")
    fig.tight_layout()
    fig.savefig(output_path)
    return output_path


if __name__ == "__main__":
    history = run_demo()
    image_path = plot_history(history)
    print(f"Saved convergence plot to {image_path}")
