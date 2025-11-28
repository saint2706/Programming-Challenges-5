"""Reusable genetic algorithm components.

This module implements basic pieces of a genetic algorithm including
population initialization, fitness evaluation, roulette-wheel selection,
one-point crossover, and mutation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence

Genome = List[float]
FitnessFunction = Callable[[Genome], float]


@dataclass
class GAConfig:
    population_size: int
    genome_length: int
    bounds: Sequence[tuple[float, float]]
    crossover_rate: float
    mutation_rate: float
    mutation_scale: float

    def __post_init__(self) -> None:
        if len(self.bounds) != self.genome_length:
            raise ValueError("bounds length must match genome_length")
        if not 0 <= self.crossover_rate <= 1:
            raise ValueError("crossover_rate must be between 0 and 1")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("mutation_rate must be between 0 and 1")
        if self.population_size < 2:
            raise ValueError("population_size must be at least 2")


@dataclass
class Individual:
    genome: Genome
    fitness: float | None = None

    def evaluate(self, fitness_fn: FitnessFunction) -> float:
        self.fitness = fitness_fn(self.genome)
        return self.fitness


class GeneticAlgorithm:
    def __init__(self, config: GAConfig, fitness_fn: FitnessFunction) -> None:
        self.config = config
        self.fitness_fn = fitness_fn
        self.population: list[Individual] = []

    def initialize_population(self) -> None:
        """Create an initial population uniformly within the provided bounds."""
        self.population = []
        for _ in range(self.config.population_size):
            genome = [random.uniform(low, high) for low, high in self.config.bounds]
            self.population.append(Individual(genome=genome))

    def evaluate_population(self) -> None:
        for individual in self.population:
            individual.evaluate(self.fitness_fn)

    def roulette_wheel_selection(self) -> Individual:
        """Select an individual proportional to its fitness.

        Fitness values are shifted if necessary to ensure non-negative
        probabilities. If all individuals have identical fitness the
        selection becomes uniform.
        """
        fitness_values = [ind.fitness for ind in self.population]
        if any(f is None for f in fitness_values):
            raise ValueError("Population must be evaluated before selection.")

        min_fitness = min(fitness_values)
        adjusted = [f - min_fitness + 1e-9 for f in fitness_values]
        total = sum(adjusted)
        if total == 0:
            return random.choice(self.population)

        pick = random.uniform(0, total)
        current = 0.0
        for individual, weight in zip(self.population, adjusted):
            current += weight
            if current >= pick:
                return individual
        return self.population[-1]

    def one_point_crossover(
        self, parent_a: Individual, parent_b: Individual
    ) -> tuple[Genome, Genome]:
        """Perform one-point crossover between two parents."""
        if (
            self.config.genome_length < 2
            or random.random() > self.config.crossover_rate
        ):
            return parent_a.genome.copy(), parent_b.genome.copy()

        point = random.randint(1, self.config.genome_length - 1)
        child1 = parent_a.genome[:point] + parent_b.genome[point:]
        child2 = parent_b.genome[:point] + parent_a.genome[point:]
        return child1, child2

    def mutate(self, genome: Genome) -> Genome:
        """Mutate a genome using gaussian noise within bounds."""
        mutated = genome.copy()
        for i, (low, high) in enumerate(self.config.bounds):
            if random.random() < self.config.mutation_rate:
                span = high - low
                mutated[i] += random.gauss(0, self.config.mutation_scale * span)
                mutated[i] = min(max(mutated[i], low), high)
        return mutated

    def step(self) -> dict[str, float]:
        """Run one generation and return summary metrics."""
        self.evaluate_population()
        best = max(self.population, key=lambda ind: ind.fitness or float("-inf"))
        avg_fitness = sum(
            ind.fitness for ind in self.population if ind.fitness is not None
        ) / len(self.population)

        next_population: list[Individual] = [
            Individual(genome=best.genome.copy(), fitness=best.fitness)
        ]
        while len(next_population) < self.config.population_size:
            parent_a = self.roulette_wheel_selection()
            parent_b = self.roulette_wheel_selection()
            child_genomes = self.one_point_crossover(parent_a, parent_b)
            for genome in child_genomes:
                if len(next_population) >= self.config.population_size:
                    break
                mutated = self.mutate(genome)
                next_population.append(Individual(genome=mutated))

        self.population = next_population
        return {
            "best_fitness": best.fitness or float("nan"),
            "avg_fitness": avg_fitness,
        }

    def run(self, generations: int) -> list[dict[str, float]]:
        """Run the genetic algorithm for a set number of generations."""
        if not self.population:
            self.initialize_population()
        history: list[dict[str, float]] = []
        for _ in range(generations):
            metrics = self.step()
            history.append(metrics)
        return history


def mean(iterable: Iterable[float]) -> float:
    items = list(iterable)
    return sum(items) / len(items) if items else 0.0
