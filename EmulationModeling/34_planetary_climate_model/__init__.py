"""Planetary climate toy models using simple energy balance equations."""

from .climate_model import (
    ClimateResult,
    LatitudinalEnergyBalanceModel,
    ZeroDEnergyBalanceModel,
)

__all__ = [
    "ZeroDEnergyBalanceModel",
    "LatitudinalEnergyBalanceModel",
    "ClimateResult",
]
