"""
Emulation/Modeling project implementation.
"""

import unittest
from model import SIRModel, Agent

class TestSIRModel(unittest.TestCase):
    """
    Docstring for TestSIRModel.
    """
    def test_initial_state(self):
        """
        Docstring for test_initial_state.
        """
        model = SIRModel(num_agents=10)
        stats = model.get_stats()
        self.assertEqual(stats["I"], 1) # Patient zero
        self.assertEqual(stats["S"], 9)
        self.assertEqual(stats["R"], 0)

    def test_infection_spread(self):
        # Place infected agent next to susceptible
        """
        Docstring for test_infection_spread.
        """
        model = SIRModel(num_agents=2, width=10, height=10, infection_radius=100, infection_prob=1.0)
        # Agent 0 is I. Agent 1 is S.
        # Force positions close
        model.agents[0].pos[:] = [5, 5]
        model.agents[1].pos[:] = [5, 5]

        model.step()

        stats = model.get_stats()
        self.assertEqual(stats["I"], 2)
        self.assertEqual(stats["S"], 0)

    def test_recovery(self):
        """
        Docstring for test_recovery.
        """
        model = SIRModel(num_agents=1, recovery_time=2)
        # Agent 0 is I, timer=2.

        model.step() # timer becomes 1
        self.assertEqual(model.agents[0].state, "I")

        model.step() # timer becomes 0 -> Recovered
        self.assertEqual(model.agents[0].state, "R")

if __name__ == '__main__':
    unittest.main()
