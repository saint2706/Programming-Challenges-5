import importlib
import os
import shutil
import sys
import unittest
from pathlib import Path

import pytest

# Check if Tkinter GUI is available (may not work in CI/headless environments)
try:
    import tkinter

    tkinter.Tk().destroy()
    TKINTER_AVAILABLE = True
except Exception:
    TKINTER_AVAILABLE = False
# Get repository root for imports
ROOT = Path(__file__).resolve().parents[2]
EMULATION_DIR = ROOT / "EmulationModeling"

# Ensure paths are set up
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(EMULATION_DIR) not in sys.path:
    sys.path.insert(0, str(EMULATION_DIR))


def import_challenge_module(challenge_num, module_name):
    base_dir = EMULATION_DIR
    dirs = [d for d in os.listdir(base_dir) if d.startswith(f"{challenge_num}_")]
    if not dirs:
        raise ImportError(f"Could not find challenge {challenge_num} directory")
    dir_name = dirs[0]
    module_path = f"EmulationModeling.{dir_name}.{module_name}"
    return importlib.import_module(module_path)


class TestEconomy(unittest.TestCase):
    def setUp(self):
        self.output_dir = "tests/EmulationModeling/output_41"
        os.makedirs(self.output_dir, exist_ok=True)

        self.main_module = import_challenge_module(41, "main")
        self.models_module = import_challenge_module(41, "models")
        self.EconomyModel = self.main_module.EconomyModel
        self.EconomyConfig = self.models_module.EconomyConfig

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_economy_runs(self):
        config = self.EconomyConfig(duration=20, output_dir=f"../../{self.output_dir}")
        model = self.EconomyModel(config)
        model.run(steps=20)

        self.assertTrue(len(model.firms) > 0)
        self.assertTrue(len(model.households) > 0)
        # Check history recorded
        self.assertGreater(len(model.history_avg_price), 0)


@pytest.mark.skipif(not TKINTER_AVAILABLE, reason="Tkinter not available")
class TestMicroservices(unittest.TestCase):
    def setUp(self):
        self.output_dir = "tests/EmulationModeling/output_42"
        os.makedirs(self.output_dir, exist_ok=True)

        self.main_module = import_challenge_module(42, "main")
        self.models_module = import_challenge_module(42, "models")
        self.MicroserviceSimulation = self.main_module.MicroserviceSimulation
        self.MicroserviceConfig = self.models_module.MicroserviceConfig

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_microservices_run(self):
        config = self.MicroserviceConfig(
            duration=10, output_dir=f"../../{self.output_dir}"
        )
        sim = self.MicroserviceSimulation(config)
        sim.run(until=10)

        self.assertTrue("Gateway" in sim.services)
        self.assertGreaterEqual(sim.services["Gateway"].stats["requests"], 0)


if __name__ == "__main__":
    unittest.main()
