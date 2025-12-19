"""
Pytest configuration for test discovery and module path setup.

This conftest.py dynamically creates module aliases to allow tests to import
modules from directories that have spaces or special characters in their names.
It maps Python-style package names (CamelCase, no spaces) to actual directory names.
"""

import importlib.util
import sys
import types
from pathlib import Path

# Repository root directory
ROOT = Path(__file__).resolve().parents[1]

# Add root to sys.path for imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add EmulationModeling for simulation_core imports
EMULATION_DIR = ROOT / "EmulationModeling"
if EMULATION_DIR.exists() and str(EMULATION_DIR) not in sys.path:
    sys.path.insert(0, str(EMULATION_DIR))

# Mapping of expected import names to actual directory names
# Format: (parent_category, python_module_name, actual_directory_name)
MODULE_MAPPINGS = [
    # Practical modules - import as Practical.ModuleName -> Practical/Directory Name
    ("Practical", "DotfilesManager", "Dotfiles Manager"),
    ("Practical", "MediaLibraryOrganizer", "Media Library Organizer"),
    ("Practical", "PersonalAPIKeyVault", "Personal API Key Vault"),
    ("Practical", "PasswordDataBreachChecker", "Password Data Breach Checker"),
    ("Practical", "PersonalTimeTracker", "Personal Time Tracker"),
    ("Practical", "SmartExpenseSplitter", "Smart Expense Splitter"),
    ("Practical", "StaticSiteGenerator", "Static Site Generator"),
    ("Practical", "TerminalHabitCoach", "Terminal Habit Coach"),
    # Algorithmic modules - import as Algorithmic.ModuleName -> Algorithmic/Directory Name
    ("Algorithmic", "ApproximateStringMatching", "Approximate String Matching"),
    ("Algorithmic", "AutocompleteEngine", "Autocomplete Engine"),
    ("Algorithmic", "TopKFrequentItems", "Top-K Frequent Items in Stream"),
    ("Algorithmic", "RandomizedAlgorithmsSuite", "Randomized Algorithms Suite"),
    ("Algorithmic", "MatrixAlgorithmLab", "Matrix Algorithm Lab"),
    ("Algorithmic", "ApproximateSetMembership", "Approximate Set Membership"),
    ("Algorithmic", "ConsistentHashingLibrary", "Consistent Hashing Library"),
    ("Algorithmic", "AdvancedIntervalScheduler", "Advanced Interval Scheduler"),
    ("Algorithmic", "ImageSeamCarving", "Image Seam Carving"),
    ("Algorithmic", "PolygonTriangulation", "Polygon Triangulation"),
    ("Algorithmic", "RegexEngine", "Regex Engine"),
    ("Algorithmic", "RoutePlanning", "Route Planning with Constraints"),
    ("Algorithmic", "SubsequenceAutomaton", "Subsequence Automaton"),
    ("Algorithmic", "VersionedKVStore", "Versioned Key-Value Store"),
    ("Algorithmic", "DynamicConnectivity", "Dynamic Connectivity Structure"),
    ("Algorithmic", "MapLabelPlacement", "Map Label Placement"),
    ("Algorithmic", "MultidimensionalIndex", "Multidimensional Index"),
    ("Algorithmic", "AutoCompletionLM", "Auto-Completion with Language Model Prior"),
    ("Algorithmic", "KdTreeNearestNeighbors", "K-d Tree & Nearest Neighbors"),
]


def create_module_alias(parent_name: str, alias_name: str, actual_dir: Path):
    """
    Create a module alias that points to an actual directory.
    This allows imports like `from Practical.DotfilesManager import X`
    when the actual directory is `Practical/Dotfiles Manager`.
    """
    full_alias = f"{parent_name}.{alias_name}"

    # Ensure parent module exists in sys.modules
    if parent_name not in sys.modules:
        parent_path = ROOT / parent_name
        if parent_path.exists():
            parent_init = parent_path / "__init__.py"
            if parent_init.exists():
                spec = importlib.util.spec_from_file_location(
                    parent_name, parent_init
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[parent_name] = module
                    spec.loader.exec_module(module)
            else:
                # Create empty module
                sys.modules[parent_name] = types.ModuleType(parent_name)

    # Skip if already exists
    if full_alias in sys.modules:
        return

    # Add actual directory to path if not already there
    actual_path_str = str(actual_dir)
    if actual_dir.exists() and actual_path_str not in sys.path:
        sys.path.insert(0, actual_path_str)

    # Check for __init__.py in the actual directory
    init_file = actual_dir / "__init__.py"
    if init_file.exists():
        try:
            spec = importlib.util.spec_from_file_location(
                full_alias, init_file, submodule_search_locations=[str(actual_dir)]
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                module.__path__ = [str(actual_dir)]
                sys.modules[full_alias] = module
                spec.loader.exec_module(module)

                # Also add as attribute to parent module
                if parent_name in sys.modules:
                    setattr(sys.modules[parent_name], alias_name, module)
        except Exception:
            pass  # Skip if module can't be loaded
    else:
        # Create a namespace package pointing to this directory
        ns_module = types.ModuleType(full_alias)
        ns_module.__path__ = [str(actual_dir)]
        ns_module.__file__ = None
        sys.modules[full_alias] = ns_module

        # Also add as attribute to parent module
        if parent_name in sys.modules:
            setattr(sys.modules[parent_name], alias_name, ns_module)


# Apply all module mappings
for parent, alias, actual_name in MODULE_MAPPINGS:
    actual_dir = ROOT / parent / actual_name
    if actual_dir.exists():
        create_module_alias(parent, alias, actual_dir)

# Add direct module paths for modules that use simple imports
# (e.g., `from approximate_set_membership.bloom import X`)
DIRECT_PATH_MODULES = [
    ROOT / "Algorithmic" / "Approximate Set Membership",
    ROOT / "Algorithmic" / "Consistent Hashing Library",
    ROOT / "Algorithmic" / "Advanced Interval Scheduler",
    ROOT / "Algorithmic" / "Top-K Frequent Items in Stream",
    ROOT / "EmulationModeling" / "14_simple_blockchain",
    ROOT / "EmulationModeling" / "simulation_core",
    ROOT / "ArtificialIntelligence",
]

for module_path in DIRECT_PATH_MODULES:
    path_str = str(module_path)
    if module_path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)

# Add all category directories to path for fallback imports
for category in ["Practical", "Algorithmic", "EmulationModeling", "ArtificialIntelligence"]:
    category_path = ROOT / category
    if category_path.exists() and str(category_path) not in sys.path:
        sys.path.insert(0, str(category_path))

# Create module aliases for directories with pythonic names (underscores instead of dashes)
# This handles cases like `approximate_set_membership` -> `Approximate Set Membership`
UNDERSCORE_ALIASES = [
    ("approximate_set_membership", ROOT / "Algorithmic" / "Approximate Set Membership"),
    ("consistent_hashing", ROOT / "Algorithmic" / "Consistent Hashing Library"),
]

for alias_name, actual_dir in UNDERSCORE_ALIASES:
    if alias_name not in sys.modules and actual_dir.exists():
        init_file = actual_dir / "__init__.py"
        if init_file.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    alias_name, init_file, submodule_search_locations=[str(actual_dir)]
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    module.__path__ = [str(actual_dir)]
                    sys.modules[alias_name] = module
                    spec.loader.exec_module(module)
            except Exception:
                pass
