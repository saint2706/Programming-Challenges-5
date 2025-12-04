import simpy
from typing import Generator, Callable, Any
import logging

logger = logging.getLogger(__name__)

class DiscreteEventSimulation:
    def __init__(self, config_seed: int = 42):
        self.env = simpy.Environment()
        self.seed = config_seed
        # Ensure reproducibility if needed by derived classes
        import random
        random.seed(config_seed)
        import numpy as np
        np.random.seed(config_seed)

    def run(self, until: float):
        logger.info(f"Starting simulation until {until}")
        self.env.run(until=until)
        logger.info("Simulation finished")

    def schedule_process(self, process_func: Callable[..., Generator[Any, Any, Any]], *args, **kwargs):
        return self.env.process(process_func(*args, **kwargs))
