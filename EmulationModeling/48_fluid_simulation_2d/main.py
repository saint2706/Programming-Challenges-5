import numpy as np
from simulation_core.pde_solvers import advect_step_2d, diffusion_step_2d

from .models import Fluid2DConfig

# Simplified "Stable Fluids" Implementation
# Based on Jos Stam's paper, adapted for Python/NumPy


class Fluid2DSimulation:
    def __init__(self, config: Fluid2DConfig):
        self.config = config
        self.N = config.grid_size
        self.dt = config.dt

        # Velocity
        self.u = np.zeros((self.N, self.N))
        self.v = np.zeros((self.N, self.N))
        self.u_prev = np.zeros((self.N, self.N))
        self.v_prev = np.zeros((self.N, self.N))

        # Density
        self.dens = np.zeros((self.N, self.N))
        self.dens_prev = np.zeros((self.N, self.N))

        # Initialize with some sources
        center = self.N // 2
        self.dens[center - 5 : center + 5, center - 5 : center + 5] = 1.0
        self.u[center - 5 : center + 5, center - 5 : center + 5] = 1.0  # Initial push
        self.v[center - 5 : center + 5, center - 5 : center + 5] = 1.0

    def step(self):
        # 1. Velocity Step
        # Add Sources (omitted for now)
        # Diffuse
        # self.u = diffusion_step_2d(self.u_prev, self.config.viscosity, self.dt, 1.0, 1.0)
        # self.v = diffusion_step_2d(self.v_prev, self.config.viscosity, self.dt, 1.0, 1.0)

        # Project (mass conservation) - simplified divergence removal?
        # Implementing a full Poisson solver is complex.
        # For "PDE-lite", let's stick to Advection-Diffusion which shows swirl if initialized right.

        # Advect
        self.u = advect_step_2d(self.u, self.u, self.v, self.dt, 1.0, 1.0)
        self.v = advect_step_2d(self.v, self.u, self.v, self.dt, 1.0, 1.0)

        # 2. Density Step
        # Diffuse
        self.dens = diffusion_step_2d(
            self.dens, self.config.diffusion, self.dt, 1.0, 1.0
        )
        # Advect
        self.dens = advect_step_2d(self.dens, self.u, self.v, self.dt, 1.0, 1.0)

        # Decay
        self.dens *= 0.995

    def run(self):
        steps = int(self.config.duration / self.dt)
        for i in range(steps):
            self.step()

            # Add some noise/inflow
            if i % 10 == 0:
                center = self.N // 2
                self.dens[center, center] = 1.0
                self.u[center, center] += np.random.uniform(-1, 1)
                self.v[center, center] += np.random.uniform(-1, 1)

        print(
            f"Final density summary: min={self.dens.min():.3f} "
            f"max={self.dens.max():.3f} mean={self.dens.mean():.3f}"
        )


def run_simulation():
    config = Fluid2DConfig(duration=10.0)
    sim = Fluid2DSimulation(config)
    sim.run()


if __name__ == "__main__":
    run_simulation()
