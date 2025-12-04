import importlib
import os
import shutil
import unittest


def import_challenge_module(challenge_num, module_name):
    base_dir = "EmulationModeling"
    dirs = [d for d in os.listdir(base_dir) if d.startswith(f"{challenge_num}_")]
    if not dirs:
        raise ImportError(f"Could not find challenge {challenge_num} directory")
    dir_name = dirs[0]
    module_path = f"{base_dir}.{dir_name}.{module_name}"
    return importlib.import_module(module_path)


class TestChallenges43_45(unittest.TestCase):
    def setUp(self):
        self.output_base = "tests/EmulationModeling/output"
        os.makedirs(self.output_base, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.output_base):
            shutil.rmtree(self.output_base)

    def test_railway(self):
        mod_main = import_challenge_module(43, "main")
        mod_models = import_challenge_module(43, "models")

        config = mod_models.RailwayConfig(
            duration=10, output_dir=f"../../{self.output_base}/43"
        )
        sim = mod_main.RailwaySimulation(config)
        sim.run(until=10)
        self.assertEqual(len(sim.trains), 3)

    def test_boot(self):
        mod_main = import_challenge_module(44, "main")
        mod_models = import_challenge_module(44, "models")

        config = mod_models.BootConfig(
            duration=5, output_dir=f"../../{self.output_base}/44"
        )
        sim = mod_main.BootSimulation(config)
        sim.run(until=5)
        self.assertTrue("BIOS" in sim.stages)

    def test_pipes(self):
        mod_main = import_challenge_module(45, "main")
        mod_models = import_challenge_module(45, "models")

        config = mod_models.PipeConfig(
            duration=1, output_dir=f"../../{self.output_base}/45"
        )
        sim = mod_main.PipeSimulation(config)
        # Should run without error
        sim.run()
        self.assertTrue(sim.state[0] > 90)  # Source pressure maintained


if __name__ == "__main__":
    unittest.main()
