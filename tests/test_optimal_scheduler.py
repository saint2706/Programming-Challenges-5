"""Tests for the optimal weighted interval scheduling algorithms."""

import itertools
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Advanced Interval Scheduler"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_scheduler import (  # noqa: E402
    Interval,
    max_intervals,
    schedule,
    schedule_binary_search,
    schedule_integer_endpoints,
    schedule_k_machines,
)


def brute_force(triples, machines=1):
    """Exhaustive maximum-weight feasible subset. Exponential; small inputs only."""
    best = 0.0
    n = len(triples)
    for mask in range(1 << n):
        chosen = [triples[i] for i in range(n) if mask >> i & 1]
        events = []
        for s, e, _ in chosen:
            if s != e:
                events.append((s, 1))
                events.append((e, -1))
        events.sort()
        running = 0
        ok = True
        for _, delta in events:
            running += delta
            if running > machines:
                ok = False
                break
        if ok:
            best = max(best, sum(float(w) for _, _, w in chosen))
    return best


def random_intervals(rng, n, span=30, max_len=8):
    out = []
    for _ in range(n):
        s = rng.randrange(0, span)
        out.append((s, s + rng.randrange(1, max_len), rng.randrange(1, 20)))
    return out


# --------------------------------------------------------------------------
# Correctness of the one-machine sweep
# --------------------------------------------------------------------------


def test_documented_example():
    result = schedule([(1, 3, 5), (2, 5, 6), (4, 6, 5), (6, 7, 8)])
    assert result.total_weight == 18.0
    assert [(i.start, i.end) for i in result.selected] == [(1, 3), (4, 6), (6, 7)]


def test_half_open_intervals_touching_at_a_point_are_compatible():
    """[1,5) and [5,9) must both be selectable; a closed-interval reading would
    take only one of them."""
    result = schedule([(1, 5, 10), (5, 9, 10)])
    assert result.total_weight == 20.0
    assert len(result.selected) == 2


def test_sweep_matches_brute_force_on_random_instances():
    rng = random.Random(1234)
    for _ in range(120):
        triples = random_intervals(rng, rng.randrange(1, 11))
        expected = brute_force(triples)
        assert schedule(triples).total_weight == pytest.approx(expected)


def test_all_three_one_machine_implementations_agree():
    rng = random.Random(99)
    for _ in range(60):
        triples = random_intervals(rng, rng.randrange(1, 40), span=100)
        a = schedule(triples).total_weight
        b = schedule_binary_search(triples).total_weight
        c = schedule_integer_endpoints(triples).total_weight
        assert a == pytest.approx(b) == pytest.approx(c)


def test_returned_selection_is_feasible_and_sums_to_the_reported_weight():
    rng = random.Random(7)
    for _ in range(40):
        triples = random_intervals(rng, rng.randrange(1, 60), span=120)
        result = schedule(triples)
        assert result.is_feasible(machines=1)
        assert sum(i.weight for i in result.selected) == pytest.approx(
            result.total_weight
        )


def test_negative_coordinates_are_handled():
    result = schedule([(-10, -5, 3), (-5, 0, 4), (-8, -2, 6)])
    assert result.total_weight == 7.0
    assert result.is_feasible()


def test_empty_and_singleton_inputs():
    assert schedule([]).total_weight == 0.0
    assert schedule([]).selected == []
    assert schedule([(0, 1, 5)]).total_weight == 5.0


def test_zero_length_intervals_never_conflict():
    result = schedule([(3, 3, 5), (3, 3, 7)])
    assert result.total_weight == 12.0


def test_interval_rejects_inverted_endpoints():
    with pytest.raises(ValueError):
        Interval(5, 2, 1.0)


def test_float_endpoints_are_rejected_with_a_pointer_to_the_alternative():
    with pytest.raises(TypeError):
        schedule([(0.5, 1.5, 3)])
    # ...and the comparison-based implementation accepts them.
    assert schedule_binary_search([(0.5, 1.5, 3)]).total_weight == 3.0


# --------------------------------------------------------------------------
# The unweighted greedy
# --------------------------------------------------------------------------


def test_greedy_is_optimal_when_weights_are_equal():
    rng = random.Random(4242)
    for _ in range(80):
        n = rng.randrange(1, 11)
        triples = [(s, e, 1) for s, e, _ in random_intervals(rng, n)]
        assert max_intervals(triples).total_weight == pytest.approx(
            brute_force(triples)
        )


def test_greedy_is_not_optimal_once_weights_differ():
    """The counterexample that justifies the DP existing at all."""
    triples = [(0, 10, 100), (0, 1, 1), (2, 3, 1)]
    assert max_intervals(triples).total_weight == 2.0  # picks the two short ones
    assert schedule(triples).total_weight == 100.0


# --------------------------------------------------------------------------
# k parallel machines
# --------------------------------------------------------------------------


def test_k_machines_reduces_to_the_sweep_at_k_equals_one():
    rng = random.Random(11)
    for _ in range(40):
        triples = random_intervals(rng, rng.randrange(1, 12))
        assert schedule_k_machines(triples, 1).total_weight == pytest.approx(
            schedule(triples).total_weight
        )


def test_k_machines_matches_brute_force():
    rng = random.Random(555)
    for machines in (2, 3):
        for _ in range(40):
            triples = random_intervals(rng, rng.randrange(1, 9), span=12, max_len=5)
            result = schedule_k_machines(triples, machines)
            assert result.total_weight == pytest.approx(brute_force(triples, machines))
            assert result.is_feasible(machines)


def test_k_machines_selects_everything_when_capacity_allows():
    triples = [(0, 10, 5), (0, 10, 5), (0, 10, 5)]
    assert schedule_k_machines(triples, 3).total_weight == 15.0
    assert schedule_k_machines(triples, 2).total_weight == 10.0


def test_k_machines_rejects_invalid_machine_counts():
    with pytest.raises(ValueError):
        schedule_k_machines([(0, 1, 1)], 0)


def test_k_machines_leaves_unprofitable_intervals_out():
    """Min-cost flow must stop augmenting rather than fill every machine."""
    result = schedule_k_machines([(0, 5, 10), (0, 5, 0.0)], 2)
    assert result.total_weight == pytest.approx(10.0)
    assert len(result.selected) == 1


# --------------------------------------------------------------------------
# NumPy fast path
# --------------------------------------------------------------------------


def test_numpy_path_agrees_with_the_list_path():
    np = pytest.importorskip("numpy")
    from optimal_scheduler import schedule_arrays

    rng = random.Random(31337)
    for _ in range(30):
        triples = random_intervals(rng, rng.randrange(1, 50), span=200)
        starts = np.array([t[0] for t in triples], dtype=np.int64)
        ends = np.array([t[1] for t in triples], dtype=np.int64)
        weights = np.array([t[2] for t in triples], dtype=np.float64)

        total, indices = schedule_arrays(starts, ends, weights)
        expected = schedule(triples)
        assert total == pytest.approx(expected.total_weight)
        assert sum(triples[i][2] for i in indices.tolist()) == pytest.approx(total)
        # The selection must itself be conflict-free.
        picked = sorted((triples[i][0], triples[i][1]) for i in indices.tolist())
        for (_, e), (s2, _) in itertools.pairwise(picked):
            assert e <= s2


def test_numpy_path_handles_empty_input():
    pytest.importorskip("numpy")
    from optimal_scheduler import schedule_arrays

    total, indices = schedule_arrays([], [], [])
    assert total == 0.0
    assert len(indices) == 0
