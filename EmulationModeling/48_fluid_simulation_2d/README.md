# Fluid Simulation (2D Navier-Stokes-lite)

Grid-based fluid simulation solving advection and diffusion equations.

## How to Run

```bash
python EmulationModeling/48_fluid_simulation_2d/main.py
```

## Logic

1.  **Grid**: 2D arrays for Density (`dens`) and Velocity (`u`, `v`).
2.  **Advection**: Moving density along velocity field. Implemented in `simulation_core/pde_solvers.py` using Numba.
3.  **Diffusion**: Spreading density over time.
4.  **Projection**: (Simplified/Omitted) Enforcing incompressibility.
5.  **Visualization**: Heatmap of density evolving over time.
