from simulation_core.config import BaseSimulationConfig


class RailwayConfig(BaseSimulationConfig):
    num_blocks: int = 10
    num_trains: int = 3
    block_length: float = 1000.0  # meters
    train_speed: float = 20.0  # m/s
    simulation_speed: float = 1.0
