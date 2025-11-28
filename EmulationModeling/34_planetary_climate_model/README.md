# Planetary Climate Toy Model

This module implements a simple planetary climate simulator using classic
energy balance equations. Two flavors are included:

1. **Zero-dimensional model**: treats the planet as a single point and balances
   absorbed solar radiation against outgoing thermal infrared. A greenhouse
   factor traps a fraction of the outgoing infrared.
2. **1D latitudinal model**: divides the planet into latitude bands that each
   receive scaled insolation and exchange heat via a diffusive term.

Both models iterate temperatures forward in time until the energy budget
reaches equilibrium.

## Key equations

- Absorbed solar energy (global mean):
  \[(1 - \alpha) \times S / 4\]
- Outgoing longwave radiation: \[\epsilon\,\sigma T^4\]
- Greenhouse factor: only a fraction `(1 - g)` of the outgoing infrared
  escapes to space.

Where `\alpha` is albedo, `S` is the solar constant, `g` is the greenhouse
factor, `\epsilon` is emissivity, and `\sigma` is the
Stefan–Boltzmann constant.

## Usage

```python
from EmulationModeling.34_planetary_climate_model import (
    ZeroDEnergyBalanceModel,
    LatitudinalEnergyBalanceModel,
)

# Zero-dimensional equilibrium
z = ZeroDEnergyBalanceModel(albedo=0.29, greenhouse_factor=0.25, initial_temperature=280)
result = z.run_to_equilibrium()
print(f"Converged: {result.converged} in {result.steps} steps; final T = {result.temperatures[-1]:.2f} K")

# Latitudinal equilibrium across 18 zones
lat_model = LatitudinalEnergyBalanceModel(n_zones=18, greenhouse_factor=0.28)
lat_result = lat_model.run_to_equilibrium(tolerance=5e-3)
print(f"Band temperatures (K): {lat_result.temperatures[-1]}")
```

## Running the demo

A small CLI demonstrates both models with adjustable parameters:

```bash
python EmulationModeling/34_planetary_climate_model/demo.py --steps 5000 --zones 18 --plot
```

The script prints equilibrium temperatures and, when `--plot` is provided,
saves a `latitudinal_profile.png` showing the final 1D temperature structure.
