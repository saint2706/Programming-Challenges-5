import unittest
import os
import shutil
import importlib

def import_challenge_module(challenge_num, module_name):
    base_dir = "EmulationModeling"
    dirs = [d for d in os.listdir(base_dir) if d.startswith(f"{challenge_num}_")]
    if not dirs:
        raise ImportError(f"Could not find challenge {challenge_num} directory")
    dir_name = dirs[0]
    module_path = f"{base_dir}.{dir_name}.{module_name}"
    return importlib.import_module(module_path)

class TestChallenges46_47(unittest.TestCase):
    def setUp(self):
        self.output_base = "tests/EmulationModeling/output"
        os.makedirs(self.output_base, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.output_base):
            shutil.rmtree(self.output_base)

    def test_robot_swarm(self):
        mod_main = import_challenge_module(46, "main")
        mod_models = import_challenge_module(46, "models")

        config = mod_models.RobotSwarmConfig(duration=2, output_dir=f"../../{self.output_base}/46", num_robots=10)
        sim = mod_main.RobotSwarmSimulation(config)
        sim.run()
        # Verify positions updated
        self.assertEqual(len(sim.positions), 10)

    def test_drones(self):
        mod_main = import_challenge_module(47, "main")
        mod_models = import_challenge_module(47, "models")

        config = mod_models.DroneConfig(duration=5, output_dir=f"../../{self.output_base}/47", num_drones=2)
        sim = mod_main.DroneSimulation(config)
        sim.run(until=5)
        self.assertEqual(len(sim.drones), 2)
        # Check graph exists
        self.assertIsNotNone(sim.graph)

if __name__ == "__main__":
    unittest.main()
