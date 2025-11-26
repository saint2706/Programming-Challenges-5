from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence

import numpy as np


@dataclass
class Agent:
    """Represents a pedestrian with a position, velocity, and destination."""

    position: np.ndarray
    velocity: np.ndarray
    destination: np.ndarray


class CrowdSimulation:
    """Simulates pedestrians moving toward their goals while avoiding others."""

    def __init__(
        self,
        num_agents: int = 25,
        width: float = 20.0,
        height: float = 20.0,
        goal_strength: float = 1.5,
        personal_space_radius: float = 2.0,
        repulsion_strength: float = 2.5,
        max_speed: float = 2.0,
        dt: float = 0.1,
        random_seed: int | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.goal_strength = goal_strength
        self.personal_space_radius = personal_space_radius
        self.repulsion_strength = repulsion_strength
        self.max_speed = max_speed
        self.dt = dt
        self.random = random.Random(random_seed)

        self.agents: List[Agent] = self._create_agents(num_agents)

    def _create_agents(self, num_agents: int) -> List[Agent]:
        agents: List[Agent] = []
        for _ in range(num_agents):
            position = np.array(
                [self.random.uniform(0, self.width), self.random.uniform(0, self.height)],
                dtype=float,
            )
            destination = np.array(
                [self.random.uniform(0, self.width), self.random.uniform(0, self.height)],
                dtype=float,
            )
            velocity = np.zeros(2, dtype=float)
            agents.append(Agent(position=position, velocity=velocity, destination=destination))
        return agents

    def _goal_force(self, agent: Agent) -> np.ndarray:
        direction = agent.destination - agent.position
        distance = np.linalg.norm(direction)
        if distance < 1e-8:
            return np.zeros(2)
        return (direction / distance) * self.goal_strength

    def _repulsive_force(self, agent: Agent, neighbors: Sequence[Agent]) -> np.ndarray:
        force = np.zeros(2)
        for other in neighbors:
            if other is agent:
                continue
            offset = agent.position - other.position
            distance = np.linalg.norm(offset)
            if distance <= 1e-8 or distance > self.personal_space_radius:
                continue
            direction = offset / distance
            strength = self.repulsion_strength * (1 - (distance / self.personal_space_radius))
            force += direction * strength / max(distance, 1e-6)
        return force

    def _update_agent(self, agent: Agent, neighbors: Sequence[Agent]) -> None:
        acceleration = self._goal_force(agent) + self._repulsive_force(agent, neighbors)
        agent.velocity = agent.velocity + acceleration * self.dt

        speed = np.linalg.norm(agent.velocity)
        if speed > self.max_speed:
            agent.velocity = (agent.velocity / speed) * self.max_speed

        agent.position = agent.position + agent.velocity * self.dt
        agent.position[0] = min(max(agent.position[0], 0.0), self.width)
        agent.position[1] = min(max(agent.position[1], 0.0), self.height)

    def step(self) -> None:
        """Advance the simulation by one time step."""

        # Copy state to avoid mid-step interference
        current_agents = [Agent(a.position.copy(), a.velocity.copy(), a.destination.copy()) for a in self.agents]
        for agent in self.agents:
            self._update_agent(agent, current_agents)

    def positions(self) -> np.ndarray:
        return np.array([agent.position for agent in self.agents])

    def destinations(self) -> np.ndarray:
        return np.array([agent.destination for agent in self.agents])

    def reset_destinations(self, destinations: Sequence[Sequence[float]]) -> None:
        if len(destinations) != len(self.agents):
            raise ValueError("Destination count must match number of agents.")
        for agent, dest in zip(self.agents, destinations):
            agent.destination = np.array(dest, dtype=float)

    def reset_positions(self, positions: Sequence[Sequence[float]]) -> None:
        if len(positions) != len(self.agents):
            raise ValueError("Position count must match number of agents.")
        for agent, pos in zip(self.agents, positions):
            agent.position = np.array(pos, dtype=float)
            agent.velocity = np.zeros(2, dtype=float)


def simulate_steps(sim: CrowdSimulation, steps: int) -> List[np.ndarray]:
    """Run the simulation for a number of steps and return the position history."""

    history: List[np.ndarray] = []
    for _ in range(steps):
        sim.step()
        history.append(sim.positions().copy())
    return history
