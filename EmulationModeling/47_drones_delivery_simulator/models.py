from simulation_core.config import BaseSimulationConfig


class DroneConfig(BaseSimulationConfig):
    num_drones: int = 5
    num_orders: int = 20
    map_size: int = 50
    battery_capacity: float = 100.0
    drone_speed: float = 2.0
