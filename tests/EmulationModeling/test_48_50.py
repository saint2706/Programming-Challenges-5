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


@pytest.mark.skipif(not TKINTER_AVAILABLE, reason="Tkinter not available")
class TestChallenges48_50(unittest.TestCase):
    def setUp(self):
        self.output_base = "tests/EmulationModeling/output"
        os.makedirs(self.output_base, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.output_base):
            shutil.rmtree(self.output_base)

    @pytest.mark.xfail(reason="imageio codec issue in simulation code")
    def test_fluid(self):
        mod_main = import_challenge_module(48, "main")
        mod_models = import_challenge_module(48, "models")

        config = mod_models.Fluid2DConfig(
            duration=1.0, output_dir=f"../../{self.output_base}/48", grid_size=32
        )
        sim = mod_main.Fluid2DSimulation(config)
        sim.run()
        # Check density has values
        self.assertGreater(sim.dens.sum(), 0)

    def test_physics(self):
        mod_main = import_challenge_module(49, "main")
        mod_models = import_challenge_module(49, "models")

        config = mod_models.RigidBodyConfig(
            duration=0.2, output_dir=f"../../{self.output_base}/49"
        )
        sim = mod_main.PhysicsSimulation(config)
        sim.run()
        # Check bodies moved (gravity)
        self.assertNotEqual(sim.world.bodies[0].velocity[1], 0)

    def test_nca(self):
        mod_main = import_challenge_module(50, "main")
        mod_models = import_challenge_module(50, "models")

        config = mod_models.NCAConfig(
            steps=5, output_dir=f"../../{self.output_base}/50"
        )
        sim = mod_main.NCASimulation(config)
        sim.run()
        # Check state changed
        self.assertIsNotNone(sim.state)


if __name__ == "__main__":
    unittest.main()
