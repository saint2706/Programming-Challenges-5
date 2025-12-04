from pydantic import Field
from simulation_core.config import BaseSimulationConfig


class EconomyConfig(BaseSimulationConfig):
    num_households: int = 50
    num_firms: int = 10
    initial_money: float = 1000.0
    wage_base: float = 50.0
    price_base: float = 10.0
    productivity_growth: float = 0.01
