"""
Emulation/Modeling project implementation.
"""

import numpy as np

class Agent:
    """
    Docstring for Agent.
    """
    def __init__(self, x, y, bounds, speed=1.0):
        """
        Docstring for __init__.
        """
        self.pos = np.array([x, y], dtype=np.float64)
        angle = np.random.uniform(0, 2*np.pi)
        self.vel = np.array([np.cos(angle), np.sin(angle)]) * speed
        self.bounds = bounds # (width, height)
        self.state = "S" # S, I, R
        self.infection_timer = 0

    def update(self):
        """
        Docstring for update.
        """
        self.pos += self.vel

        # Bounce off walls
        if self.pos[0] < 0 or self.pos[0] > self.bounds[0]:
            self.vel[0] *= -1
            self.pos[0] = np.clip(self.pos[0], 0, self.bounds[0])

        if self.pos[1] < 0 or self.pos[1] > self.bounds[1]:
            self.vel[1] *= -1
            self.pos[1] = np.clip(self.pos[1], 0, self.bounds[1])

class SIRModel:
    """
    Docstring for SIRModel.
    """
    def __init__(self, num_agents=100, width=100, height=100, infection_radius=5.0, infection_prob=0.5, recovery_time=100):
        """
        Docstring for __init__.
        """
        self.width = width
        self.height = height
        self.agents = [Agent(np.random.rand()*width, np.random.rand()*height, (width, height)) for _ in range(num_agents)]
        self.infection_radius = infection_radius
        self.infection_prob = infection_prob
        self.recovery_time = recovery_time

        # Patient zero
        self.agents[0].state = "I"
        self.agents[0].infection_timer = recovery_time

    def step(self):
        # Move agents
        """
        Docstring for step.
        """
        for agent in self.agents:
            agent.update()

            if agent.state == "I":
                agent.infection_timer -= 1
                if agent.infection_timer <= 0:
                    agent.state = "R"

        # Check infections
        # O(N^2) naive check
        # Optimize with spatial hash if needed, but N=100-200 is fine.
        infected = [a for a in self.agents if a.state == "I"]
        susceptible = [a for a in self.agents if a.state == "S"]

        for i_agent in infected:
            for s_agent in susceptible:
                dist = np.linalg.norm(i_agent.pos - s_agent.pos)
                if dist < self.infection_radius:
                    if np.random.random() < self.infection_prob:
                        s_agent.state = "I"
                        s_agent.infection_timer = self.recovery_time

    def get_stats(self):
        """
        Docstring for get_stats.
        """
        counts = {"S": 0, "I": 0, "R": 0}
        for a in self.agents:
            counts[a.state] += 1
        return counts
