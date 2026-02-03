# Planetary Climate Toy Model

This module implements a simple planetary climate simulator using classic energy balance equations.

## 📋 Table of Contents

- [Theory](#theory)
- [Usage](#usage)
- [Running the Demo](#running-the-demo)

## 🧠 Theory

### Model Variants

1. **Zero-dimensional model**: treats the planet as a single point and balances absorbed solar radiation against outgoing thermal infrared.
2. **1D latitudinal model**: divides the planet into latitude bands that receive scaled insolation and exchange heat via diffusion.

### Key Equations

- Absorbed solar energy (global mean):
  \[(1 - \alpha) \times S / 4\]
- Outgoing longwave radiation:
  \[\epsilon\,\sigma T^4\]
- Greenhouse factor: only a fraction `(1 - g)` of outgoing infrared escapes to space.

Where `\alpha` is albedo, `S` is the solar constant, `g` is the greenhouse factor, `\epsilon` is emissivity, and `\sigma` is the Stefan–Boltzmann constant.

### Ideal Example Test Case (Exercises Edge Cases)

**Scenario:**
- Solar constant `S = 1361`
- Albedo `\alpha = 0.35` (high reflectivity)
- Greenhouse factor `g = 0.0` (no greenhouse effect)
- Emissivity `\epsilon = 0.95`
- Latitudinal zones `n = 4` (coarse grid)
- Initial temperature `T0 = 320 K` (warm start)

This case tests:
- **Strong cooling** due to high albedo and no greenhouse effect.
- **Coarse discretization** in the 1D model (edge case for diffusion).
- **Large temperature correction** from a warm initial state.

### Step-by-Step Walkthrough

#### Zero-Dimensional Model
1. **Initialize** temperature at 320 K.
2. **Compute absorbed energy** using high albedo, reducing incoming solar power.
3. **Compute outgoing radiation** using `\epsilon\sigma T^4`.
4. **Update temperature**: energy deficit causes the temperature to drop.
5. **Iterate until convergence**: successive steps reduce the temperature change below tolerance.

#### Latitudinal Model
1. **Initialize** 4 latitude bands with 320 K.
2. **Apply insolation profile**: equatorial zones receive more energy than polar zones.
3. **Apply diffusion**: heat flows from warmer to cooler bands.
4. **Update each band** with local energy imbalance.
5. **Converge** once every band’s temperature change is within tolerance.

This example demonstrates convergence from an extreme initial condition and highlights diffusion’s role in smoothing band temperatures.

## 🚀 Usage

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

## 🧪 Running the Demo

```bash
python EmulationModeling/34_planetary_climate_model/demo.py --steps 5000 --zones 18
```

The script prints equilibrium temperatures for both models.
