"""
Emulation/Modeling project implementation.
"""

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from simulation import CrowdSimulation


class TestCrowdSimulation(unittest.TestCase):
    """
    Docstring for TestCrowdSimulation.
    """
    def test_goal_force_moves_agent_forward(self):
        """
        Docstring for test_goal_force_moves_agent_forward.
        """
        sim = CrowdSimulation(num_agents=1, goal_strength=1.0, dt=1.0, random_seed=1)
        sim.reset_positions([[0.0, 0.0]])
        sim.reset_destinations([[5.0, 0.0]])

        sim.step()

        agent = sim.agents[0]
        self.assertGreater(agent.velocity[0], 0)
        self.assertGreater(agent.position[0], 0)

    def test_repulsion_pushes_agents_apart(self):
        """
        Docstring for test_repulsion_pushes_agents_apart.
        """
        sim = CrowdSimulation(
            num_agents=2,
            personal_space_radius=3.0,
            repulsion_strength=5.0,
            goal_strength=0.0,
            dt=1.0,
            random_seed=1,
        )
        sim.reset_positions([[5.0, 5.0], [6.0, 5.0]])
        sim.reset_destinations([[5.0, 5.0], [6.0, 5.0]])

        sim.step()

        a0, a1 = sim.agents
        self.assertLess(a0.position[0], 5.0)
        self.assertGreater(a1.position[0], 6.0)

    def test_speed_is_capped(self):
        """
        Docstring for test_speed_is_capped.
        """
        sim = CrowdSimulation(num_agents=1, goal_strength=10.0, max_speed=0.5, dt=1.0, random_seed=1)
        sim.reset_positions([[0.0, 0.0]])
        sim.reset_destinations([[100.0, 0.0]])

        sim.step()

        speed = (sim.agents[0].velocity**2).sum() ** 0.5
        self.assertLessEqual(speed, 0.5)


if __name__ == "__main__":
    unittest.main()
