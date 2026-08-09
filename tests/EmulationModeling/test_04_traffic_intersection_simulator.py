import importlib
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

run_simulation = importlib.import_module(
    "EmulationModeling.04_traffic_intersection_simulator.simulation"
).run_simulation


class TestTrafficSimulation(unittest.TestCase):
    def test_run_simulation(self):
        stats = run_simulation(duration=100)
        self.assertIn("arrived", stats)
        self.assertIn("crossed", stats)
        # Even with randomness, in 100 ticks with arrival rate 0.2, some cars should arrive
        # expected ~20 cars
        self.assertGreater(stats["arrived"], 0)

    def test_traffic_flow(self):
        # Run longer to ensure some cross
        stats = run_simulation(duration=500)
        self.assertGreater(stats["crossed"], 0)
        self.assertTrue(stats["arrived"] >= stats["crossed"])


if __name__ == "__main__":
    unittest.main()
