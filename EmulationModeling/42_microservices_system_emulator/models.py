from pydantic import Field
from simulation_core.config import BaseSimulationConfig

class MicroserviceConfig(BaseSimulationConfig):
    num_services: int = 5
    request_rate: float = 2.0  # requests per second
    failure_rate: float = 0.05
    mean_latency: float = 0.1
    max_retries: int = 3
