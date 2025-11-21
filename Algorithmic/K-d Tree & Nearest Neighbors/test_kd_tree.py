"""Tests and benchmarks for the K-d Tree implementation."""

import importlib.util
import math
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Dynamic import to handle script execution from various contexts
THIS_DIR = Path(__file__).resolve().parent
MODULE_PATH = THIS_DIR / "kd_tree.py"

# We need to import kd_tree dynamically because of its location relative to root
spec = importlib.util.spec_from_file_location("kd_tree", MODULE_PATH)
if spec and spec.loader:
    kd_tree = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = kd_tree
    spec.loader.exec_module(kd_tree)
else:
    raise ImportError(f"Could not import kd_tree from {MODULE_PATH}")

random.seed(1234)


def generate_points(n: int, dims: int) -> List[List[float]]:
    """Generate random points in n-dimensional space."""
    return [[random.uniform(-100, 100) for _ in range(dims)] for _ in range(n)]


def test_tree_balances_with_median_split() -> None:
    """Verify that the tree is reasonably balanced."""
    print("Testing tree balance...")
    points = generate_points(255, 5)
    root = kd_tree.build_kd_tree(points)

    height = kd_tree.tree_height(root)
    expected_log_height = math.ceil(math.log2(len(points) + 1))
    # Strict balance isn't guaranteed, but shouldn't be degenerate
    assert height <= expected_log_height * 2
    assert kd_tree.count_nodes(root) == len(points)
    print("✓ Tree balance OK")


def test_nearest_neighbor_matches_brute_force() -> None:
    """Verify nearest neighbor accuracy against brute force."""
    print("Testing Nearest Neighbor accuracy...")
    points = generate_points(200, 4)
    query = generate_points(1, 4)[0]

    root = kd_tree.build_kd_tree(points)
    kd_point, kd_dist = kd_tree.nearest_neighbor(root, query)
    brute_point, brute_dist = kd_tree.brute_force_nearest(points, query)

    # Points might differ if distances are identical, so check distance primarily
    assert math.isclose(kd_dist, brute_dist, rel_tol=1e-9)
    print("✓ Nearest Neighbor OK")


def test_k_nearest_neighbors_matches_brute_force() -> None:
    """Verify k-NN accuracy against brute force."""
    print("Testing k-NN accuracy...")
    points = generate_points(500, 3)
    query = generate_points(1, 3)[0]

    root = kd_tree.build_kd_tree(points)
    k = 7
    kd_results = kd_tree.k_nearest_neighbors(root, query, k)
    brute_results = kd_tree.brute_force_k_nearest(points, query, k)

    # Compare distances
    kd_dists = [d for _, d in kd_results]
    brute_dists = [d for _, d in brute_results]

    assert len(kd_dists) == len(brute_dists)
    for d1, d2 in zip(kd_dists, brute_dists):
         assert math.isclose(d1, d2, rel_tol=1e-9)

    print("✓ k-NN OK")


def benchmark_search_performance(
    num_points: int = 3000, dims: int = 4, queries: int = 200, k: int = 3
) -> Tuple[float, float]:
    """Run performance benchmark comparing K-d Tree vs Brute Force."""
    print(f"\nBenchmarking: {num_points} points, {dims} dims, {queries} queries...")
    points = generate_points(num_points, dims)
    root = kd_tree.build_kd_tree(points)
    query_points = generate_points(queries, dims)

    # K-d Tree
    start = time.perf_counter()
    for q in query_points:
        kd_tree.nearest_neighbor(root, q)
        kd_tree.k_nearest_neighbors(root, q, k)
    kd_duration = time.perf_counter() - start

    # Brute Force
    start = time.perf_counter()
    for q in query_points:
        kd_tree.brute_force_nearest(points, q)
        kd_tree.brute_force_k_nearest(points, q, k)
    brute_duration = time.perf_counter() - start

    return kd_duration, brute_duration


if __name__ == "__main__":
    print("🧪 RUNNING TESTS")
    print("=" * 40)
    test_tree_balances_with_median_split()
    test_nearest_neighbor_matches_brute_force()
    test_k_nearest_neighbors_matches_brute_force()

    print("\n🚀 RUNNING BENCHMARKS")
    print("=" * 40)
    kd_time, brute_time = benchmark_search_performance()
    print(f"KD-tree time:    {kd_time:.4f}s")
    print(f"Brute force time: {brute_time:.4f}s")

    if kd_time < brute_time:
        speedup = brute_time / kd_time
        print(f"Speedup: {speedup:.2f}x faster")
    else:
        print("K-d Tree was slower (this can happen for high dims or small N)")
