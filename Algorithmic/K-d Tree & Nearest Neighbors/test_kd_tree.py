import importlib.util
import math
import random
import statistics
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
MODULE_PATH = THIS_DIR / "kd_tree.py"

spec = importlib.util.spec_from_file_location("kd_tree", MODULE_PATH)
kd_tree = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = kd_tree
spec.loader.exec_module(kd_tree)

random.seed(1234)


def generate_points(n: int, dims: int):
    return [[random.uniform(-100, 100) for _ in range(dims)] for _ in range(n)]


def test_tree_balances_with_median_split():
    points = generate_points(255, 5)
    root = kd_tree.build_kd_tree(points)

    height = kd_tree.tree_height(root)
    expected_log_height = math.ceil(math.log2(len(points) + 1))
    assert height <= expected_log_height * 2
    assert kd_tree.count_nodes(root) == len(points)


def test_nearest_neighbor_matches_brute_force():
    points = generate_points(200, 4)
    query = generate_points(1, 4)[0]

    root = kd_tree.build_kd_tree(points)
    kd_point, kd_dist = kd_tree.nearest_neighbor(root, query)
    brute_point, brute_dist = kd_tree.brute_force_nearest(points, query)

    assert kd_point == brute_point
    assert math.isclose(kd_dist, brute_dist, rel_tol=1e-9)


def test_k_nearest_neighbors_matches_brute_force():
    points = generate_points(500, 3)
    query = generate_points(1, 3)[0]

    root = kd_tree.build_kd_tree(points)
    k = 7
    kd_results = kd_tree.k_nearest_neighbors(root, query, k)
    brute_results = kd_tree.brute_force_k_nearest(points, query, k)

    assert [p for p, _ in kd_results] == [p for p, _ in brute_results]
    assert [round(d, 10) for _, d in kd_results] == [round(d, 10) for _, d in brute_results]


def benchmark_search_performance(num_points=3000, dims=4, queries=200, k=3):
    points = generate_points(num_points, dims)
    root = kd_tree.build_kd_tree(points)
    query_points = generate_points(queries, dims)

    start = time.perf_counter()
    for q in query_points:
        kd_tree.nearest_neighbor(root, q)
        kd_tree.k_nearest_neighbors(root, q, k)
    kd_duration = time.perf_counter() - start

    start = time.perf_counter()
    for q in query_points:
        kd_tree.brute_force_nearest(points, q)
        kd_tree.brute_force_k_nearest(points, q, k)
    brute_duration = time.perf_counter() - start

    return kd_duration, brute_duration


def test_kd_tree_beats_brute_force_on_average():
    kd_duration, brute_duration = benchmark_search_performance()

    # Allow some headroom for environment noise but expect a clear advantage.
    assert kd_duration < brute_duration * 0.8


if __name__ == "__main__":
    kd_time, brute_time = benchmark_search_performance()
    print(f"KD-tree time: {kd_time:.4f}s for batched queries")
    print(f"Brute force time: {brute_time:.4f}s for batched queries")
