"""Particle system engine supporting list-based and vectorized updates.

This module provides a simple particle engine with two update implementations:
- A straightforward Python list-based update for readability and easier extension.
- A NumPy-vectorized update path for higher throughput on larger particle counts.

A sample animation using ``matplotlib`` is available when running this module as a
script (``python particle_engine.py``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib import colors as mcolors


@dataclass
class Particle:
    """A single particle with position, velocity, and remaining lifetime."""

    position: np.ndarray
    velocity: np.ndarray
    lifetime: float

    def is_alive(self) -> bool:
        """Return ``True`` if the particle still has time left."""

        return self.lifetime > 0


@dataclass
class ParticleEngine:
    """Manage a set of particles and advance them through time."""

    gravity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    particles: List[Particle] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Docstring for __post_init__.
        """
        self.gravity = np.asarray(self.gravity, dtype=float)
        if self.gravity.shape != (2,):
            raise ValueError("Gravity must be a 2D vector")

    def add_particles(
        self, positions: Iterable[Sequence[float]], velocities: Iterable[Sequence[float]], lifetimes: Iterable[float]
    ) -> None:
        """Add multiple particles to the engine.

        Args:
            positions: Iterable of ``(x, y)`` position pairs.
            velocities: Iterable of ``(vx, vy)`` velocity pairs.
            lifetimes: Iterable of lifetimes in seconds.
        """

        for pos, vel, life in zip(positions, velocities, lifetimes):
            self.particles.append(
                Particle(position=np.asarray(pos, dtype=float), velocity=np.asarray(vel, dtype=float), lifetime=float(life))
            )

    def update(self, dt: float, use_vectorized: bool = False) -> None:
        """Advance the simulation by ``dt`` seconds.

        Args:
            dt: Time step in seconds.
            use_vectorized: When ``True``, use the NumPy vectorized update path.
        """

        if use_vectorized:
            self._update_vectorized(dt)
        else:
            self._update_list(dt)

    def _update_list(self, dt: float) -> None:
        """Update particles using a standard Python list iteration."""

        alive: List[Particle] = []
        for particle in self.particles:
            particle.velocity += self.gravity * dt
            particle.position += particle.velocity * dt
            particle.lifetime -= dt
            if particle.is_alive():
                alive.append(particle)
        self.particles = alive

    def _update_vectorized(self, dt: float) -> None:
        """Update particles using NumPy vector operations."""

        if not self.particles:
            return

        positions = np.array([p.position for p in self.particles], dtype=float)
        velocities = np.array([p.velocity for p in self.particles], dtype=float)
        lifetimes = np.array([p.lifetime for p in self.particles], dtype=float)

        velocities += self.gravity * dt
        positions += velocities * dt
        lifetimes -= dt

        alive_mask = lifetimes > 0
        positions = positions[alive_mask]
        velocities = velocities[alive_mask]
        lifetimes = lifetimes[alive_mask]

        self.particles = [
            Particle(position=pos, velocity=vel, lifetime=life)
            for pos, vel, life in zip(positions, velocities, lifetimes)
        ]

    def positions(self) -> np.ndarray:
        """Return an ``(n, 2)`` array of particle positions."""

        if not self.particles:
            return np.empty((0, 2))
        return np.stack([p.position for p in self.particles])

    def lifetimes(self) -> np.ndarray:
        """Return an array of particle lifetimes."""

        if not self.particles:
            return np.empty((0,))
        return np.array([p.lifetime for p in self.particles])


# -------- Sample animation -------- #

def _initialize_particles(engine: ParticleEngine, count: int = 250) -> None:
    """
    Docstring for _initialize_particles.
    """
    rng = np.random.default_rng()
    positions = rng.normal(loc=0.0, scale=0.2, size=(count, 2))
    velocities = rng.normal(loc=0.0, scale=1.5, size=(count, 2))
    lifetimes = rng.uniform(2.0, 5.0, size=(count,))
    engine.add_particles(positions=positions, velocities=velocities, lifetimes=lifetimes)


def run_sample_animation() -> None:
    """Run a matplotlib animation of the particle engine.

    The animation uses the vectorized update path for efficiency. Adjust the
    parameters below to experiment with gravity, particle count, and lifespan.
    """

    engine = ParticleEngine(gravity=np.array([0.0, -3.5]))
    _initialize_particles(engine)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_title("Particle System (Vectorized Update)")
    base_color = np.array(mcolors.to_rgba("tab:blue"))
    scatter = ax.scatter([], [], s=25, c=[base_color])

    def init():
        """
        Docstring for init.
        """
        scatter.set_offsets(np.empty((0, 2)))
        scatter.set_array(np.array([]))
        return (scatter,)

    def update(frame: int):
        # Use a fixed timestep for stability in the animation.
        """
        Docstring for update.
        """
        engine.update(dt=0.05, use_vectorized=True)
        positions = engine.positions()
        lifetimes = engine.lifetimes()
        alphas = np.clip(lifetimes / 5.0, 0.0, 1.0)

        scatter.set_offsets(positions)
        if len(alphas):
            colors = np.tile(base_color, (len(alphas), 1))
            colors[:, -1] = alphas
            scatter.set_facecolors(colors)
        else:
            scatter.set_offsets(np.empty((0, 2)))
        return (scatter,)

    ani = FuncAnimation(fig, update, init_func=init, interval=30, blit=True)
    plt.show()


if __name__ == "__main__":
    run_sample_animation()
