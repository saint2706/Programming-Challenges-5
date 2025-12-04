import random
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from simulation_core.agent_based import Agent, AgentBasedModel
from simulation_core.visualization import SimulationVisualizer

from .models import EconomyConfig


class Household(Agent):
    def __init__(self, agent_id: int, money: float):
        super().__init__(agent_id)
        self.money = money
        self.consumption = 0
        self.labor_supply = 1.0  # Works 1 unit
        self.employed_at = None

    def step(self, model: "EconomyModel"):
        # 1. Earn wages
        if self.employed_at:
            wage = self.employed_at.wage
            self.money += wage

        # 2. Consume goods
        # Choose cheapest firm with stock
        firms_with_stock = [f for f in model.firms if f.inventory > 0]
        if firms_with_stock:
            firms_with_stock.sort(key=lambda f: f.price)
            chosen_firm = firms_with_stock[0]

            if self.money >= chosen_firm.price:
                self.money -= chosen_firm.price
                chosen_firm.sell_product()
                self.consumption += 1


class Firm(Agent):
    def __init__(self, agent_id: int, money: float, wage: float, price: float):
        super().__init__(agent_id)
        self.money = money
        self.wage = wage
        self.price = price
        self.inventory = 0
        self.employees: List[Household] = []
        self.sales = 0

    def step(self, model: "EconomyModel"):
        # 1. Production
        # Production function: Y = A * L
        production = len(self.employees) * (
            1.0 + model.time * model.config.productivity_growth
        )
        self.inventory += production

        # 2. Pay wages
        wage_bill = len(self.employees) * self.wage
        if self.money >= wage_bill:
            self.money -= wage_bill
        else:
            # Bankrupt / Fire people
            if self.employees:
                fired = self.employees.pop()
                fired.employed_at = None

        # 3. Adjust Prices & Wages based on last step sales
        # Simple heuristic
        if self.sales > production * 0.8:
            self.price *= 1.05  # Raise price if high demand
            self.wage *= 1.02  # Raise wage to attract more
        elif self.sales < production * 0.2:
            self.price *= 0.95  # Lower price
            if self.price < self.wage:
                self.price = self.wage * 1.01  # floor

        self.sales = 0  # Reset for next step

    def sell_product(self):
        self.inventory -= 1
        self.sales += 1
        self.money += self.price


class EconomyModel(AgentBasedModel):
    def __init__(self, config: EconomyConfig):
        super().__init__(config.seed)
        self.config = config
        self.households: List[Household] = []
        self.firms: List[Firm] = []
        self.visualizer = SimulationVisualizer(
            output_dir=f"EmulationModeling/41_economy_market_simulator/{config.output_dir}"
        )

        self.history_avg_price = []
        self.history_avg_wage = []

        self.setup()

    def setup(self):
        # Create Firms
        for i in range(self.config.num_firms):
            f = Firm(i, 10000, self.config.wage_base, self.config.price_base)
            self.firms.append(f)
            self.add_agent(f)

        # Create Households and assign random jobs
        for i in range(self.config.num_households):
            h = Household(100 + i, self.config.initial_money)
            employer = random.choice(self.firms)
            employer.employees.append(h)
            h.employed_at = employer
            self.households.append(h)
            self.add_agent(h)

    def step(self):
        super().step()

        # Collect Stats
        avg_price = np.mean([f.price for f in self.firms])
        avg_wage = np.mean([f.wage for f in self.firms])

        self.history_avg_price.append(avg_price)
        self.history_avg_wage.append(avg_wage)

        if self.time % 10 == 0:
            self.snapshot()

    def snapshot(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))

        ax1.plot(self.history_avg_price, label="Avg Price")
        ax1.plot(self.history_avg_wage, label="Avg Wage")
        ax1.set_title("Market Trends")
        ax1.legend()

        wealths = [h.money for h in self.households]
        ax2.hist(wealths, bins=10, color="skyblue", edgecolor="black")
        ax2.set_title("Wealth Distribution")

        self.visualizer.add_frame(fig)
        plt.close(fig)


def run_simulation():
    config = EconomyConfig(duration=100)
    model = EconomyModel(config)
    model.run(steps=int(config.duration))
    model.visualizer.save_gif("market_dynamics.gif")


if __name__ == "__main__":
    run_simulation()
