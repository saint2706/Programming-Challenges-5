from simulation_core.config import BaseSimulationConfig


class RobotSwarmConfig(BaseSimulationConfig):
    num_robots: int = 100
    width: float = 100.0
    height: float = 100.0
    perception_radius: float = 10.0
    alignment_weight: float = 1.0
    cohesion_weight: float = 0.5
    separation_weight: float = 1.5
    max_speed: float = 2.0
