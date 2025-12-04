from simulation_core.config import BaseSimulationConfig

class NCAConfig(BaseSimulationConfig):
    grid_size: int = 40
    channels: int = 16
    hidden_size: int = 64
    steps: int = 200
    target_emoji: str = "🦎" # Just for metadata
