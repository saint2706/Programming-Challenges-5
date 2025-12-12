"""
Pytest configuration for test discovery and module path setup.

This conftest.py adds module directories to sys.path to allow tests to import
modules from directories that have spaces in their names.
"""

import sys
from pathlib import Path

# Repository root directory
ROOT = Path(__file__).resolve().parents[1]

# Add root to sys.path for imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add all module directories to sys.path for direct imports
MODULE_PATHS = [
    # Practical modules
    ROOT / "Practical" / "Dotfiles Manager",
    ROOT / "Practical" / "Media Library Organizer",
    ROOT / "Practical" / "Personal API Key Vault",
    ROOT / "Practical" / "Password Data Breach Checker",
    ROOT / "Practical" / "Personal Time Tracker",
    ROOT / "Practical" / "Smart Expense Splitter",
    ROOT / "Practical" / "Static Site Generator",
    ROOT / "Practical" / "Terminal Habit Coach",
    ROOT / "Practical" / "Universal Log Analyzer",
    # Algorithmic modules
    ROOT / "Algorithmic" / "Approximate String Matching",
    ROOT / "Algorithmic" / "Autocomplete Engine",
    ROOT / "Algorithmic" / "Top-K Frequent Items in Stream",
    ROOT / "Algorithmic" / "Randomized Algorithms Suite",
    ROOT / "Algorithmic" / "Matrix Algorithm Lab",
    ROOT / "Algorithmic" / "Approximate Set Membership",
    ROOT / "Algorithmic" / "Consistent Hashing Library",
    ROOT / "Algorithmic" / "Advanced Interval Scheduler",
    # EmulationModeling modules
    ROOT / "EmulationModeling" / "14_simple_blockchain",
    ROOT / "EmulationModeling" / "simulation_core",
    # ArtificialIntelligence modules
    ROOT / "ArtificialIntelligence",
]

for module_path in MODULE_PATHS:
    path_str = str(module_path)
    if module_path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)

# Also add Practical and Algorithmic directories themselves for package imports
for category in ["Practical", "Algorithmic", "EmulationModeling", "ArtificialIntelligence"]:
    category_path = ROOT / category
    if category_path.exists() and str(category_path) not in sys.path:
        sys.path.insert(0, str(category_path))

