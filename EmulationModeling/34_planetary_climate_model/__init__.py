"""Planetary climate toy models using simple energy balance equations."""

from .climate_model import ZeroDEnergyBalanceModel, LatitudinalEnergyBalanceModel, ClimateResult

__all__ = [
    "ZeroDEnergyBalanceModel",
    "LatitudinalEnergyBalanceModel",
    "ClimateResult",
]
