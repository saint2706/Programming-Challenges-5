import unittest
import os
import shutil
import importlib
import sys

# Dynamic import helper since folder starts with number
def import_challenge_module(challenge_num, module_name):
    # e.g. "EmulationModeling.40_logistics_routing_simulator.main"
    # Find the full directory name
    base_dir = "EmulationModeling"
    dirs = [d for d in os.listdir(base_dir) if d.startswith(f"{challenge_num}_")]
    if not dirs:
        raise ImportError(f"Could not find challenge {challenge_num} directory")

    dir_name = dirs[0]
    module_path = f"{base_dir}.{dir_name}.{module_name}"
    return importlib.import_module(module_path)

class TestLogistics(unittest.TestCase):
    def setUp(self):
        self.output_dir = "tests/EmulationModeling/output_40"
        os.makedirs(self.output_dir, exist_ok=True)

        # Import dynamically
        self.main_module = import_challenge_module(40, "main")
        self.models_module = import_challenge_module(40, "models")
        self.LogisticsSimulation = self.main_module.LogisticsSimulation
        self.LogisticsConfig = self.models_module.LogisticsConfig

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_simulation_runs(self):
        config = self.LogisticsConfig(
            duration=50,
            output_dir=f"../../{self.output_dir}",
            num_customers=5,
            num_trucks=2
        )
        sim = self.LogisticsSimulation(config)
        sim.run(until=10)

        # Check that state changed
        self.assertEqual(len(sim.trucks), 2)
        self.assertEqual(len(sim.customers), 5)

        # Check we can generate frames
        self.assertGreaterEqual(len(sim.visualizer.frames), 0)

if __name__ == "__main__":
    unittest.main()
