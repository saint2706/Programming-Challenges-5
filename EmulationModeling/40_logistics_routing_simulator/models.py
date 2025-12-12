from simulation_core.config import BaseSimulationConfig


class LogisticsConfig(BaseSimulationConfig):
    num_depots: int = 2
    num_customers: int = 10
    num_trucks: int = 5
    truck_capacity: int = 100
    map_size: int = 1000  # 1000x1000 grid
    simulation_speed: float = 1.0
