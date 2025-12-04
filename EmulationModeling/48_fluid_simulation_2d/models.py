from simulation_core.config import BaseSimulationConfig

class Fluid2DConfig(BaseSimulationConfig):
    grid_size: int = 64
    dt: float = 0.1
    diffusion: float = 0.0001
    viscosity: float = 0.0001
    iterations: int = 4
