"""
Pytest configuration for test discovery and module path setup.

This conftest.py creates symlinks to allow tests to import modules
from directories that have spaces in their names using Python-compatible
import paths.
"""

import os
import sys
from pathlib import Path

import pytest

# Repository root directory
ROOT = Path(__file__).resolve().parents[1]

# Add root to sys.path for imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Directory mappings: import_name -> actual_directory_name
ALGORITHMIC_MAPPINGS = {
    "ApproximateStringMatching": "Approximate String Matching",
    "AutocompleteEngine": "Autocomplete Engine",
    "TopKFrequentItems": "Top-K Frequent Items in Stream",
    "RandomizedAlgorithmsSuite": "Randomized Algorithms Suite",
    "MatrixAlgorithmLab": "Matrix Algorithm Lab",
}

PRACTICAL_MAPPINGS = {
    "DotfilesManager": "Dotfiles Manager",
    "MediaLibraryOrganizer": "Media Library Organizer",
    "PasswordDataBreachChecker": "Password Data Breach Checker",
    "PersonalTimeTracker": "Personal Time Tracker",
    "SmartExpenseSplitter": "Smart Expense Splitter",
    "StaticSiteGenerator": "Static Site Generator",
    "TerminalHabitCoach": "Terminal Habit Coach",
    "UniversalLogAnalyzer": "Universal Log Analyzer",
}

# Root level mappings (import from root level)
ROOT_LEVEL_MAPPINGS = {
    "approximate_set_membership": "Algorithmic/Approximate Set Membership",
    "consistent_hashing": "Algorithmic/Consistent Hashing Library",
}


def create_symlink(link_path: Path, target_path: Path) -> None:
    """Create a symlink, removing existing one if necessary."""
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.is_dir():
            # Skip if an actual directory exists - this can happen when running
            # tests from the repo without act, or if the directory was created
            # manually. In this case, the real directory should be used.
            return
    
    if target_path.exists():
        try:
            link_path.symlink_to(target_path)
        except OSError:
            pass  # Symlink creation might fail on some systems


def setup_module_symlinks():
    """Create symlinks for all module mappings."""
    # Create Algorithmic symlinks
    algorithmic_dir = ROOT / "Algorithmic"
    for link_name, target_name in ALGORITHMIC_MAPPINGS.items():
        link_path = algorithmic_dir / link_name
        target_path = algorithmic_dir / target_name
        create_symlink(link_path, target_path)
    
    # Create Practical symlinks
    practical_dir = ROOT / "Practical"
    for link_name, target_name in PRACTICAL_MAPPINGS.items():
        link_path = practical_dir / link_name
        target_path = practical_dir / target_name
        create_symlink(link_path, target_path)
    
    # Create root level symlinks
    for link_name, target_rel_path in ROOT_LEVEL_MAPPINGS.items():
        link_path = ROOT / link_name
        target_path = ROOT / target_rel_path
        create_symlink(link_path, target_path)


# Set up symlinks when conftest is loaded
setup_module_symlinks()
