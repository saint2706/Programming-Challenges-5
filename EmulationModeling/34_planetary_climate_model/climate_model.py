"""Toy planetary climate models using simple energy balance equations.

The models here follow the classic zero-dimensional energy balance approach:

- The planet receives solar radiation reduced by its Bond albedo.
- It emits thermal infrared radiation modeled as a black body with an
  adjustable emissivity.
- A greenhouse factor retains a fraction of the outgoing infrared, reducing
  the energy that escapes to space.

The same energy accounting is extended to a 1D latitudinal model that adds a
very simple diffusive heat transport between neighboring latitude bands.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

STEFAN_BOLTZMANN = 5.670374419e-8  # W m^-2 K^-4
SOLAR_CONSTANT = 1361.0  # W m^-2 at 1 AU


@dataclass
class ClimateResult:
    """Stores the outcome of an energy balance simulation."""

    temperatures: np.ndarray
    steps: int
    converged: bool


class ZeroDEnergyBalanceModel:
    """Zero-dimensional (globally averaged) energy balance model.

    Parameters
    ----------
    solar_constant: float
        Top-of-atmosphere solar irradiance in W m^-2.
    albedo: float
        Bond albedo between 0 and 1 representing reflected solar energy.
    greenhouse_factor: float
        Fraction of outgoing infrared retained by greenhouse gases. Values in
        the range ``[0, 1)`` keep the model physically meaningful.
    emissivity: float
        Planetary emissivity for thermal radiation.
    heat_capacity: float
        Effective areal heat capacity (J m^-2 K^-1). Larger values slow
        convergence.
    dt: float
        Integration timestep in seconds.
    initial_temperature: float
        Starting guess for surface temperature in Kelvin.
    """

    def __init__(
        self,
        solar_constant: float = SOLAR_CONSTANT,
        albedo: float = 0.3,
        greenhouse_factor: float = 0.2,
        emissivity: float = 0.99,
        heat_capacity: float = 4.2e8,
        dt: float = 86_400.0,
        initial_temperature: float = 288.0,
    ) -> None:
        self.solar_constant = solar_constant
        self.albedo = albedo
        self.greenhouse_factor = greenhouse_factor
        self.emissivity = emissivity
        self.heat_capacity = heat_capacity
        self.dt = dt
        self.temperature = initial_temperature

    @property
    def absorbed_solar(self) -> float:
        """Return the globally averaged absorbed solar flux (W m^-2)."""

        return (1.0 - self.albedo) * self.solar_constant / 4.0

    def outgoing_infrared(self, temperature: float) -> float:
        """Thermal infrared flux emitted to space for a given temperature."""

        raw_olr = self.emissivity * STEFAN_BOLTZMANN * temperature**4
        return (1.0 - self.greenhouse_factor) * raw_olr

    def step(self) -> float:
        """Advance the temperature by one timestep using explicit Euler."""

        emitted = self.outgoing_infrared(self.temperature)
        net_flux = self.absorbed_solar - emitted
        self.temperature += (net_flux * self.dt) / self.heat_capacity
        return self.temperature

    def run_to_equilibrium(self, max_steps: int = 10_000, tolerance: float = 1e-4) -> ClimateResult:
        """Iterate until temperature changes fall below ``tolerance``.

        Parameters
        ----------
        max_steps: int
            Maximum number of timesteps to attempt.
        tolerance: float
            Stop when the absolute temperature change between steps is less
            than this value (Kelvin).
        """

        history: List[float] = [self.temperature]
        converged = False
        for step in range(1, max_steps + 1):
            previous = self.temperature
            current = self.step()
            history.append(current)
            if abs(current - previous) < tolerance:
                converged = True
                break
        return ClimateResult(temperatures=np.array(history), steps=len(history) - 1, converged=converged)


class LatitudinalEnergyBalanceModel:
    """Energy balance model split into latitude bands.

    Each band receives a scaled share of the solar constant based on the cosine
    of its latitude and can exchange heat with neighbors through a diffusive
    term. The greenhouse factor and albedo are applied uniformly for
    simplicity.
    """

    def __init__(
        self,
        n_zones: int = 18,
        solar_constant: float = SOLAR_CONSTANT,
        albedo: float = 0.3,
        greenhouse_factor: float = 0.2,
        emissivity: float = 0.99,
        heat_capacity: float = 4.2e8,
        meridional_diffusivity: float = 0.5,
        dt: float = 86_400.0,
        initial_temperature: float = 288.0,
    ) -> None:
        if n_zones < 2:
            raise ValueError("At least two latitude zones are required.")

        self.n_zones = n_zones
        self.latitudes = np.linspace(-90 + 90 / n_zones, 90 - 90 / n_zones, n_zones)
        self.weights = np.cos(np.radians(self.latitudes)).clip(min=0.05)
        self.insolation_scaling = self.weights / np.average(self.weights)

        self.solar_constant = solar_constant
        self.albedo = albedo
        self.greenhouse_factor = greenhouse_factor
        self.emissivity = emissivity
        self.heat_capacity = heat_capacity
        self.diffusivity = meridional_diffusivity
        self.dt = dt
        self.temperatures = np.full(n_zones, initial_temperature, dtype=float)

    @property
    def absorbed_solar(self) -> np.ndarray:
        """Return absorbed solar energy per latitude band (W m^-2)."""

        return (1.0 - self.albedo) * self.solar_constant / 4.0 * self.insolation_scaling

    def outgoing_infrared(self, temperatures: np.ndarray) -> np.ndarray:
        """Outgoing longwave radiation per band (W m^-2)."""

        raw_olr = self.emissivity * STEFAN_BOLTZMANN * temperatures**4
        return (1.0 - self.greenhouse_factor) * raw_olr

    def _diffusion_term(self, temperatures: np.ndarray) -> np.ndarray:
        """Simple second-order diffusion across latitude bands."""

        laplacian = np.zeros_like(temperatures)
        laplacian[1:-1] = temperatures[:-2] - 2 * temperatures[1:-1] + temperatures[2:]
        laplacian[0] = temperatures[1] - temperatures[0]
        laplacian[-1] = temperatures[-2] - temperatures[-1]
        return self.diffusivity * laplacian

    def step(self) -> np.ndarray:
        """Advance all latitude bands by one timestep."""

        emitted = self.outgoing_infrared(self.temperatures)
        net_flux = self.absorbed_solar - emitted + self._diffusion_term(self.temperatures)
        self.temperatures += (net_flux * self.dt) / self.heat_capacity
        return self.temperatures.copy()

    def run_to_equilibrium(self, max_steps: int = 10_000, tolerance: float = 1e-4) -> ClimateResult:
        """Iterate until the maximum temperature change drops below tolerance."""

        history: List[np.ndarray] = [self.temperatures.copy()]
        converged = False
        for step in range(1, max_steps + 1):
            previous = self.temperatures.copy()
            current = self.step()
            history.append(current)
            if np.max(np.abs(current - previous)) < tolerance:
                converged = True
                break
        return ClimateResult(temperatures=np.vstack(history), steps=len(history) - 1, converged=converged)


__all__ = [
    "ZeroDEnergyBalanceModel",
    "LatitudinalEnergyBalanceModel",
    "ClimateResult",
    "SOLAR_CONSTANT",
    "STEFAN_BOLTZMANN",
]
