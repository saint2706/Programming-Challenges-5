from simulation_core.config import BaseSimulationConfig


class RigidBodyConfig(BaseSimulationConfig):
    gravity: float = -9.81
    num_bodies: int = 5
    world_size: float = 10.0
