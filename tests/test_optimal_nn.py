"""Tests for the nearest-neighbour structures."""

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "K-d Tree & Nearest Neighbors"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from optimal_nn import (  # noqa: E402
    HNSW,
    ImplicitKdTree,
    brute_force_knn,
    recommend_structure,
)

SAMPLE = [[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]]


def naive_knn(points, query, k):
    """Sorted (index, distance) pairs. The simplest possible oracle."""
    dists = [(math.dist(p, query), i) for i, p in enumerate(points)]
    dists.sort()
    return [(i, d) for d, i in dists[:k]]


# --------------------------------------------------------------------------
# ImplicitKdTree
# --------------------------------------------------------------------------


def test_documented_example():
    tree = ImplicitKdTree(SAMPLE)
    idx, dist = tree.nearest([9, 2])
    assert SAMPLE[idx] == [8, 1]
    assert dist == pytest.approx(math.sqrt(2))


def test_kd_tree_matches_brute_force_on_random_data():
    rng = np.random.default_rng(20260831)
    for dim in (1, 2, 3, 5, 8):
        for n in (1, 2, 17, 300):
            data = rng.normal(size=(n, dim))
            tree = ImplicitKdTree(data)
            for _ in range(5):
                query = rng.normal(size=dim)
                k = min(4, n)
                got = tree.k_nearest(query, k)
                expected = naive_knn(data.tolist(), query.tolist(), k)
                assert [i for i, _ in got] == [i for i, _ in expected], (dim, n)
                for (_, a), (_, b) in zip(got, expected):
                    assert a == pytest.approx(b)


def test_kd_tree_handles_duplicate_and_collinear_points():
    """Degenerate inputs break naive median splits; the partition must cope."""
    duplicates = [[1.0, 1.0]] * 50
    tree = ImplicitKdTree(duplicates)
    hits = tree.k_nearest([1.0, 1.0], 5)
    assert len(hits) == 5
    assert all(d == pytest.approx(0.0) for _, d in hits)

    collinear = [[float(i), 0.0] for i in range(100)]
    tree = ImplicitKdTree(collinear)
    idx, dist = tree.nearest([42.4, 0.0])
    assert collinear[idx] == [42.0, 0.0]
    assert dist == pytest.approx(0.4)


def test_kd_tree_returns_all_points_when_k_exceeds_n():
    tree = ImplicitKdTree(SAMPLE)
    assert len(tree.k_nearest([0, 0], 100)) == len(SAMPLE)
    assert tree.k_nearest([0, 0], 0) == []


def test_kd_tree_results_are_sorted_by_distance():
    rng = np.random.default_rng(4)
    data = rng.normal(size=(200, 3))
    tree = ImplicitKdTree(data)
    dists = [d for _, d in tree.k_nearest(rng.normal(size=3), 10)]
    assert dists == sorted(dists)


def test_radius_search_matches_a_linear_filter():
    rng = np.random.default_rng(11)
    data = rng.normal(size=(400, 3))
    tree = ImplicitKdTree(data)
    for _ in range(10):
        query = rng.normal(size=3)
        radius = 0.8
        got = {i for i, _ in tree.within_radius(query, radius)}
        expected = {
            i
            for i, p in enumerate(data.tolist())
            if math.dist(p, query.tolist()) <= radius
        }
        assert got == expected


def test_radius_search_rejects_negative_radius():
    with pytest.raises(ValueError):
        ImplicitKdTree(SAMPLE).within_radius([0, 0], -1.0)


def test_kd_tree_rejects_malformed_input():
    with pytest.raises(ValueError):
        ImplicitKdTree([])
    with pytest.raises(ValueError):
        ImplicitKdTree(np.zeros((0, 3)))
    with pytest.raises(ValueError):
        ImplicitKdTree(SAMPLE).k_nearest([1, 2, 3], 1)


def test_split_axis_follows_the_widest_spread():
    """A long thin cloud must be split along its long axis, not a cycled one."""
    rng = np.random.default_rng(2)
    data = np.column_stack(
        [rng.normal(scale=100.0, size=500), rng.normal(scale=0.01, size=500)]
    )
    tree = ImplicitKdTree(data)
    root_axis = tree.axes[len(data) // 2]
    assert root_axis == 0, "root should split along the high-variance axis"


def test_implicit_layout_stores_no_python_nodes():
    """The structural claim: the tree is an array permutation, nothing more."""
    tree = ImplicitKdTree(np.random.default_rng(0).normal(size=(64, 3)))
    assert sorted(tree.order.tolist()) == list(range(64))
    assert len(tree.axes) == 64
    assert not hasattr(tree, "root")


# --------------------------------------------------------------------------
# brute_force_knn
# --------------------------------------------------------------------------


def test_brute_force_matches_the_oracle():
    rng = np.random.default_rng(7)
    data = rng.normal(size=(150, 6))
    probes = rng.normal(size=(12, 6))
    idx, dist = brute_force_knn(data, probes, 5)
    assert idx.shape == (12, 5)
    for row, query in enumerate(probes.tolist()):
        expected = naive_knn(data.tolist(), query, 5)
        assert idx[row].tolist() == [i for i, _ in expected]
        for got, (_, want) in zip(dist[row].tolist(), expected):
            assert got == pytest.approx(want)


def test_brute_force_distances_are_never_negative():
    """The ||p||^2 - 2p.q + ||q||^2 expansion can cancel below zero on ties."""
    data = np.ones((10, 4))
    _, dist = brute_force_knn(data, data, 3)
    assert np.all(dist >= 0.0)
    assert np.allclose(dist, 0.0)


def test_brute_force_clamps_k_and_validates_shapes():
    data = np.zeros((3, 2))
    idx, _ = brute_force_knn(data, np.zeros((1, 2)), 99)
    assert idx.shape == (1, 3)
    with pytest.raises(ValueError):
        brute_force_knn(data, np.zeros((1, 5)), 1)
    with pytest.raises(ValueError):
        brute_force_knn(data, np.zeros((1, 2)), 0)
    with pytest.raises(ValueError):
        brute_force_knn(np.zeros(3), np.zeros((1, 2)), 1)


def test_kd_tree_and_brute_force_agree_exactly():
    """Both are exact, so any disagreement is a bug in one of them."""
    rng = np.random.default_rng(99)
    data = rng.normal(size=(500, 4))
    probes = rng.normal(size=(20, 4))
    tree = ImplicitKdTree(data)
    idx, _ = brute_force_knn(data, probes, 7)
    for row, query in enumerate(probes.tolist()):
        assert [i for i, _ in tree.k_nearest(query, 7)] == idx[row].tolist()


# --------------------------------------------------------------------------
# HNSW
# --------------------------------------------------------------------------


def test_hnsw_finds_a_point_that_is_in_the_index():
    rng = np.random.default_rng(0)
    data = rng.normal(size=(400, 16))
    index = HNSW(data, m=8, ef_construction=60, seed=1)
    for probe in (0, 7, 123, 399):
        hits = index.query(data[probe], k=1, ef=80)
        assert hits[0][0] == probe
        assert hits[0][1] == pytest.approx(0.0, abs=1e-9)


def test_hnsw_recall_rises_with_ef():
    """ef is the accuracy dial and must behave monotonically enough to be useful."""
    rng = np.random.default_rng(5)
    data = rng.normal(size=(1_200, 24))
    probes = rng.normal(size=(30, 24))
    truth, _ = brute_force_knn(data, probes, 10)
    index = HNSW(data, m=12, ef_construction=80, seed=3)

    def recall(ef):
        hits = [index.query(p, 10, ef=ef) for p in probes]
        found = sum(
            len({i for i, _ in h} & set(t.tolist())) for h, t in zip(hits, truth)
        )
        return found / (len(probes) * 10)

    low, high = recall(10), recall(200)
    assert high > low
    assert high > 0.90, f"recall at ef=200 was only {high}"


def test_hnsw_results_are_sorted_and_sized():
    rng = np.random.default_rng(8)
    data = rng.normal(size=(300, 10))
    index = HNSW(data, m=8, ef_construction=50, seed=2)
    hits = index.query(rng.normal(size=10), k=5)
    assert len(hits) == 5
    assert [d for _, d in hits] == sorted(d for _, d in hits)
    assert index.query(rng.normal(size=10), k=0) == []


def test_hnsw_is_reproducible_for_a_fixed_seed():
    rng = np.random.default_rng(6)
    data = rng.normal(size=(200, 8))
    query = rng.normal(size=8)
    a = HNSW(data, m=8, ef_construction=40, seed=42).query(query, 5)
    b = HNSW(data, m=8, ef_construction=40, seed=42).query(query, 5)
    assert a == b


def test_hnsw_handles_a_single_point():
    index = HNSW([[1.0, 2.0]], m=4, ef_construction=10, seed=0)
    assert index.query([1.0, 2.0], k=3) == [(0, pytest.approx(0.0))]


def test_hnsw_rejects_malformed_input():
    with pytest.raises(ValueError):
        HNSW([])
    with pytest.raises(ValueError):
        HNSW([[1.0]], m=0)
    with pytest.raises(ValueError):
        HNSW([[1.0, 2.0]]).query([1.0])


# --------------------------------------------------------------------------
# The recommendation encodes the measured crossovers
# --------------------------------------------------------------------------


def test_recommendation_reflects_the_measured_crossover():
    assert recommend_structure(n=100_000, dim=2) == "ImplicitKdTree"
    assert recommend_structure(n=100_000, dim=3) == "ImplicitKdTree"
    # Past the measured crossover, vectorised brute force wins for exact search.
    assert recommend_structure(n=100_000, dim=32) == "brute_force_knn"
    # Small point sets never justify building anything.
    assert recommend_structure(n=50, dim=2) == "brute_force_knn"
    # Approximate results in high dimension are HNSW's regime.
    assert recommend_structure(n=100_000, dim=128, exact=False) == "HNSW"
    assert recommend_structure(n=100_000, dim=128, exact=True) == "brute_force_knn"
