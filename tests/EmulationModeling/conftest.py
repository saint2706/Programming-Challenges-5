"""Pytest configuration for EmulationModeling tests.

Sets up module paths for the simulation_core library and EmulationModeling challenges.
"""

import sys
from pathlib import Path

# Repository root directory
ROOT = Path(__file__).resolve().parents[2]

# Add EmulationModeling directory to path for simulation_core imports
EMULATION_DIR = ROOT / "EmulationModeling"
if EMULATION_DIR.exists() and str(EMULATION_DIR) not in sys.path:
    sys.path.insert(0, str(EMULATION_DIR))

# Also add root to path for EmulationModeling package imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
