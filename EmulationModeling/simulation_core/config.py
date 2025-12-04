from pydantic import BaseModel, ConfigDict


class BaseSimulationConfig(BaseModel):
    """Base configuration for simulations."""

    model_config = ConfigDict(extra="forbid")

    seed: int = 42
    output_dir: str = "output"
    duration: float = 100.0
    fps: int = 30  # For visualizations
