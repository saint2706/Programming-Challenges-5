"""Genetic algorithm demo for the Traveling Salesman Problem.

This script generates a small set of cities and uses a genetic algorithm
with order crossover and swap mutation to find a near-optimal route.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

City = Tuple[str, Tuple[float, float]]
Route = List[int]


@dataclass
class GAConfig:
    """
    Docstring for GAConfig.
    """
    population_size: int = 80
    generations: int = 200
    mutation_rate: float = 0.15
    elite_size: int = 4
    tournament_size: int = 5
    random_seed: int = 42


def euclidean_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """
    Docstring for euclidean_distance.
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def route_length(route: Sequence[int], cities: Sequence[City]) -> float:
    """
    Docstring for route_length.
    """
    distance = 0.0
    for idx, city_index in enumerate(route):
        next_city_index = route[(idx + 1) % len(route)]
        distance += euclidean_distance(cities[city_index][1], cities[next_city_index][1])
    return distance


def fitness(route: Sequence[int], cities: Sequence[City]) -> float:
    """
    Docstring for fitness.
    """
    return 1.0 / (route_length(route, cities) + 1e-9)


def initial_population(size: int, num_cities: int) -> List[Route]:
    """
    Docstring for initial_population.
    """
    base_route = list(range(num_cities))
    return [random.sample(base_route, num_cities) for _ in range(size)]


def tournament_selection(population: List[Route], cities: Sequence[City], k: int) -> Route:
    """
    Docstring for tournament_selection.
    """
    contenders = random.sample(population, k)
    return max(contenders, key=lambda route: fitness(route, cities))


def order_crossover(parent1: Route, parent2: Route) -> Route:
    """
    Docstring for order_crossover.
    """
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child = [None] * size  # type: ignore[list-item]
    child[start:end] = parent1[start:end]

    fill_positions = [i for i in range(size) if child[i] is None]
    fill_values = [city for city in parent2 if city not in child]
    for pos, value in zip(fill_positions, fill_values):
        child[pos] = value
    return child  # type: ignore[return-value]


def swap_mutation(route: Route) -> Route:
    """
    Docstring for swap_mutation.
    """
    mutated = route.copy()
    idx1, idx2 = random.sample(range(len(mutated)), 2)
    mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
    return mutated


def evolve_population(population: List[Route], config: GAConfig, cities: Sequence[City]) -> List[Route]:
    """
    Docstring for evolve_population.
    """
    population.sort(key=lambda r: fitness(r, cities), reverse=True)
    new_population: List[Route] = population[: config.elite_size]

    while len(new_population) < config.population_size:
        parent1 = tournament_selection(population, cities, config.tournament_size)
        parent2 = tournament_selection(population, cities, config.tournament_size)
        child = order_crossover(parent1, parent2)
        if random.random() < config.mutation_rate:
            child = swap_mutation(child)
        new_population.append(child)
    return new_population


def run_ga(cities: Sequence[City], config: GAConfig) -> Tuple[Route, float]:
    """
    Docstring for run_ga.
    """
    random.seed(config.random_seed)
    population = initial_population(config.population_size, len(cities))

    for _ in range(config.generations):
        population = evolve_population(population, config, cities)

    best_route = max(population, key=lambda r: fitness(r, cities))
    best_distance = route_length(best_route, cities)
    return best_route, best_distance


def format_route(route: Sequence[int], cities: Sequence[City]) -> str:
    """
    Docstring for format_route.
    """
    return " -> ".join(cities[idx][0] for idx in route)


def main() -> None:
    """
    Docstring for main.
    """
    cities: List[City] = [
        ("A", (0, 0)),
        ("B", (1, 5)),
        ("C", (5, 6)),
        ("D", (8, 3)),
        ("E", (6, -2)),
        ("F", (2, -4)),
        ("G", (-1, -3)),
        ("H", (-2, 4)),
    ]

    config = GAConfig()
    best_route, best_distance = run_ga(cities, config)

    route_names = format_route(best_route, cities)
    print("Best route found:")
    print(route_names)
    print(f"Total distance: {best_distance:.2f} units")


if __name__ == "__main__":
    main()
