from typing import List

import numpy as np


class Agent:
    def __init__(self, agent_id: int):
        self.id = agent_id

    def step(self, model: "AgentBasedModel"):
        pass


class AgentBasedModel:
    def __init__(self, seed: int = 42):
        self.agents: List[Agent] = []
        self.rng = np.random.default_rng(seed)
        self.time = 0

    def add_agent(self, agent: Agent):
        self.agents.append(agent)

    def step(self):
        self.time += 1
        # Shuffle order to avoid bias
        indices = np.arange(len(self.agents))
        self.rng.shuffle(indices)
        for i in indices:
            self.agents[i].step(self)

    def run(self, steps: int):
        for _ in range(steps):
            self.step()
