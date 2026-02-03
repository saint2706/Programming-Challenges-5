"""Weather pattern cellular model.

This module implements a simple 2D cellular model describing pressure diffusion
and wind-driven moisture transport. It exposes a :class:`WeatherGrid` for
running simulations and querying the field state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class WeatherCell:
    """Properties of a single grid cell."""

    pressure: float
    humidity: float
    wind: Tuple[float, float]


class WeatherGrid:
    """Grid holding weather state and update rules."""

    def __init__(
        self,
        width: int,
        height: int,
        diffusion_rate: float = 0.15,
        moisture_transport_rate: float = 0.1,
        dt: float = 1.0,
        seed: int | None = None,
    ) -> None:
        if width <= 1 or height <= 1:
            raise ValueError("Grid must be at least 2x2")

        self.width = width
        self.height = height
        self.diffusion_rate = diffusion_rate
        self.moisture_transport_rate = moisture_transport_rate
        self.dt = dt
        self.random = np.random.default_rng(seed)

        # Initialize fields with small perturbations for interesting dynamics.
        self.pressure = self._initialize_pressure()
        self.humidity = self._initialize_humidity()
        self.wind_x, self.wind_y = self._initialize_wind()

    def _initialize_pressure(self) -> np.ndarray:
        base = 1013.25  # standard atmosphere in hPa
        perturbation = self.random.normal(
            loc=0.0, scale=5.0, size=(self.height, self.width)
        )
        return base + perturbation

    def _initialize_humidity(self) -> np.ndarray:
        return self.random.uniform(low=0.45, high=0.8, size=(self.height, self.width))

    def _initialize_wind(self) -> Tuple[np.ndarray, np.ndarray]:
        direction = self.random.uniform(
            low=-1.0, high=1.0, size=(self.height, self.width, 2)
        )
        magnitude = self.random.uniform(
            low=0.0, high=8.0, size=(self.height, self.width, 1)
        )
        norm = np.linalg.norm(direction, axis=2, keepdims=True)
        norm = np.where(norm == 0, 1.0, norm)
        unit_dir = direction / norm
        wind_vector = unit_dir * magnitude
        return wind_vector[:, :, 0], wind_vector[:, :, 1]

    def step(self) -> None:
        """Advance the simulation by one time step."""

        self._diffuse_pressure()
        self._transport_humidity()

    def _diffuse_pressure(self) -> None:
        """Simple 4-neighbor diffusion for pressure."""

        kernel = np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, -4.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
        )
        laplacian = self._convolve(self.pressure, kernel)
        self.pressure += self.diffusion_rate * laplacian * self.dt

    def _transport_humidity(self) -> None:
        """Advection of humidity based on wind vector field."""

        grad_x = np.roll(self.humidity, -1, axis=1) - np.roll(self.humidity, 1, axis=1)
        grad_y = np.roll(self.humidity, -1, axis=0) - np.roll(self.humidity, 1, axis=0)

        advection = self.wind_x * grad_x + self.wind_y * grad_y
        self.humidity += -self.moisture_transport_rate * advection * self.dt
        self.humidity = np.clip(self.humidity, 0.0, 1.0)

    def _convolve(self, field: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply a convolution with wrap-around boundary conditions."""

        shifted = (
            np.roll(field, 1, axis=0) * kernel[2, 1]
            + np.roll(field, -1, axis=0) * kernel[0, 1]
            + np.roll(field, 1, axis=1) * kernel[1, 2]
            + np.roll(field, -1, axis=1) * kernel[1, 0]
        )
        return shifted + field * kernel[1, 1]

    def snapshot(self) -> np.ndarray:
        """Return a copy of the current pressure field."""

        return self.pressure.copy()

    def cell_at(self, row: int, col: int) -> WeatherCell:
        """Retrieve a :class:`WeatherCell` representing the current state."""

        return WeatherCell(
            pressure=float(self.pressure[row, col]),
            humidity=float(self.humidity[row, col]),
            wind=(float(self.wind_x[row, col]), float(self.wind_y[row, col])),
        )


def run_simulation(
    width: int = 64,
    height: int = 64,
    steps: int = 50,
    diffusion_rate: float = 0.15,
    moisture_transport_rate: float = 0.1,
    dt: float = 1.0,
    seed: int | None = 7,
) -> np.ndarray:
    """Run a simulation and return the final pressure field."""

    grid = WeatherGrid(
        width=width,
        height=height,
        diffusion_rate=diffusion_rate,
        moisture_transport_rate=moisture_transport_rate,
        dt=dt,
        seed=seed,
    )
    for _ in range(steps):
        grid.step()
    return grid.snapshot()
