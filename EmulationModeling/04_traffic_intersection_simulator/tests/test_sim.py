"""
Emulation/Modeling project implementation.
"""

import unittest
from simulation import run_simulation

class TestTrafficSimulation(unittest.TestCase):
    """
    Docstring for TestTrafficSimulation.
    """
    def test_run_simulation(self):
        """
        Docstring for test_run_simulation.
        """
        stats = run_simulation(duration=100)
        self.assertIn("arrived", stats)
        self.assertIn("crossed", stats)
        # Even with randomness, in 100 ticks with arrival rate 0.2, some cars should arrive
        # expected ~20 cars
        self.assertGreater(stats["arrived"], 0)

    def test_traffic_flow(self):
        # Run longer to ensure some cross
        """
        Docstring for test_traffic_flow.
        """
        stats = run_simulation(duration=500)
        self.assertGreater(stats["crossed"], 0)
        self.assertTrue(stats["arrived"] >= stats["crossed"])

if __name__ == '__main__':
    unittest.main()
