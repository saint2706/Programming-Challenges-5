"""Tests for the generic DP engine, its analysis, and the speedups it detects."""

import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Generic DP Visualizer"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_dp import (  # noqa: E402
    DP,
    analyze,
    divide_and_conquer_dp,
    edit_distance,
    knapsack,
    knuth_interval_dp,
    longest_common_subsequence,
    naive_interval_dp,
    render_html,
    satisfies_quadrangle_inequality,
)

# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------


def test_fibonacci_example_from_the_docstring():
    fib = DP(
        dependencies=lambda n: () if n < 2 else (n - 1, n - 2),
        combine=lambda n, vals: sum(vals),
        base=lambda n: n if n < 2 else None,
    )
    assert fib.solve(30).value(30) == 832040


def test_evaluation_has_no_recursion_limit():
    """A 20,000-deep chain would blow a recursive memoised implementation."""
    chain = DP(
        dependencies=lambda n: () if n == 0 else (n - 1,),
        combine=lambda n, vals: vals[0] + 1,
        base=lambda n: 0 if n == 0 else None,
    )
    depth = 20_000
    assert chain.solve(depth).value(depth) == depth


def test_only_reachable_states_are_evaluated():
    """Memoised top-down evaluation, not a full table fill."""
    problem = edit_distance("ab", "xy")
    solution = problem.solve((2, 2))
    # 3x3 grid of states is reachable; nothing outside it.
    assert set(solution.values) == {(i, j) for i in range(3) for j in range(3)}


def test_cycles_are_reported_clearly():
    cyclic = DP(
        dependencies=lambda n: (1 - n,),
        combine=lambda n, vals: vals[0],
    )
    with pytest.raises(ValueError, match="cycle"):
        cyclic.solve(0)


def test_order_is_a_valid_topological_order():
    solution = edit_distance("kitten", "sitting").solve((6, 7))
    seen = set()
    for state in solution.order:
        for dep in solution.dependencies[state]:
            assert dep in seen, f"{state} evaluated before its dependency {dep}"
        seen.add(state)


# --------------------------------------------------------------------------
# The ready-made problems produce correct answers
# --------------------------------------------------------------------------


def test_edit_distance_matches_known_values():
    for a, b, expected in [
        ("kitten", "sitting", 3),
        ("saturday", "sunday", 3),
        ("", "abc", 3),
        ("abc", "abc", 0),
    ]:
        solution = edit_distance(a, b).solve((len(a), len(b)))
        assert solution.value((len(a), len(b))) == expected


def test_lcs_matches_known_values():
    for a, b, expected in [
        ("AGGTAB", "GXTXAYB", 4),
        ("abc", "abc", 3),
        ("abc", "def", 0),
    ]:
        solution = longest_common_subsequence(a, b).solve((len(a), len(b)))
        assert solution.value((len(a), len(b))) == expected


def test_knapsack_matches_brute_force():
    rng = random.Random(11)
    for _ in range(15):
        count = rng.randrange(1, 11)
        weights = [rng.randrange(1, 12) for _ in range(count)]
        values = [rng.randrange(1, 30) for _ in range(count)]
        capacity = rng.randrange(1, 30)

        best = 0
        for mask in range(1 << count):
            chosen = [i for i in range(count) if mask >> i & 1]
            if sum(weights[i] for i in chosen) <= capacity:
                best = max(best, sum(values[i] for i in chosen))

        solution = knapsack(weights, values, capacity).solve((count, capacity))
        assert solution.value((count, capacity)) == best


def test_knapsack_rejects_mismatched_inputs():
    with pytest.raises(ValueError):
        knapsack([1, 2], [1], 10)


# --------------------------------------------------------------------------
# Analysis: the part that is supposed to be the contribution
# --------------------------------------------------------------------------


def test_edit_distance_rolling_window_is_derived_not_assumed():
    """The classic "you only need two rows" result, produced by the tool."""
    solution = edit_distance("kitten", "sitting").solve((6, 7))
    report = analyze(solution)
    assert set(report.stencil) == {(0, 1), (1, 0), (1, 1)}
    # One step back in each dimension means two live layers in each.
    assert report.rolling_window == (2, 2)
    axis, factor = report.space_saving()
    assert factor > 1.0
    assert "roll dimension" in report.summary()


def test_lcs_rolling_window_matches_edit_distance():
    solution = longest_common_subsequence("AGGTAB", "GXTXAYB").solve((6, 7))
    report = analyze(solution)
    assert report.rolling_window == (2, 2)


def test_knapsack_rolls_the_item_dimension():
    """0/1 knapsack looks back exactly one item, so two item-layers suffice."""
    weights = [3, 5, 7, 2]
    values = [4, 6, 9, 3]
    solution = knapsack(weights, values, 20).solve((4, 20))
    report = analyze(solution)
    assert report.rolling_window is not None
    assert report.rolling_window[0] == 2, "knapsack looks back one item"
    axis, _ = report.space_saving()
    assert axis == 0


def test_critical_path_bounds_available_parallelism():
    solution = edit_distance("kitten", "sitting").solve((6, 7))
    report = analyze(solution)
    # A grid DP's critical path is the anti-diagonal count.
    assert report.critical_path == 13
    assert report.peak_width >= 1
    assert report.parallel_speedup_bound == pytest.approx(
        report.states / report.critical_path
    )


def test_a_pure_chain_has_no_parallelism_at_all():
    chain = DP(
        dependencies=lambda n: () if n == 0 else (n - 1,),
        combine=lambda n, vals: vals[0] + 1,
        base=lambda n: 0 if n == 0 else None,
    )
    report = analyze(chain.solve(100))
    assert report.critical_path == report.states == 101
    assert report.peak_width == 1
    assert report.parallel_speedup_bound == pytest.approx(1.0)


def test_analysis_degrades_gracefully_on_non_grid_states():
    """States that are not integer tuples get graph metrics but no stencil."""
    problem = DP(
        dependencies=lambda s: () if len(s) <= 1 else (s[1:],),
        combine=lambda s, vals: vals[0] + 1,
        base=lambda s: 0 if len(s) <= 1 else None,
    )
    report = analyze(problem.solve("abcdef"))
    assert report.states == 6
    assert report.stencil == ()
    assert report.rolling_window is None
    assert report.space_saving() is None
    assert "no rolling-array" not in report.summary()


# --------------------------------------------------------------------------
# Asymptotic speedups
# --------------------------------------------------------------------------


def prefix_sums(counts):
    out = [0]
    for value in counts:
        out.append(out[-1] + value)
    return out


def test_quadrangle_inequality_holds_for_a_prefix_sum_cost():
    prefix = prefix_sums([3, 1, 4, 1, 5, 9, 2, 6])

    def cost(i, j):
        return float(prefix[j] - prefix[i])

    assert satisfies_quadrangle_inequality(cost, len(prefix))


def test_quadrangle_inequality_rejects_a_cost_that_violates_it():
    # A concave (rather than convex) cost breaks the inequality.
    def cost(i, j):
        return -float((j - i) ** 2)

    assert not satisfies_quadrangle_inequality(cost, 8)


def test_quadrangle_inequality_sampling_agrees_with_exhaustive():
    prefix = prefix_sums([2, 7, 1, 8, 2, 8, 1, 8, 2, 8])

    def cost(i, j):
        return float(prefix[j] - prefix[i])

    assert satisfies_quadrangle_inequality(cost, len(prefix))
    assert satisfies_quadrangle_inequality(cost, len(prefix), sample=200)


def test_knuth_optimisation_agrees_with_the_naive_cubic_dp():
    rng = random.Random(7)
    for _ in range(10):
        n = rng.randrange(2, 40)
        prefix = prefix_sums([rng.randrange(1, 30) for _ in range(n)])

        def cost(i, j, prefix=prefix):
            return float(prefix[j] - prefix[i])

        assert satisfies_quadrangle_inequality(cost, n, sample=300)
        assert math.isclose(naive_interval_dp(n, cost), knuth_interval_dp(n, cost))


def test_interval_dp_handles_degenerate_sizes():
    assert naive_interval_dp(0, lambda i, j: 1.0) == 0.0
    assert naive_interval_dp(1, lambda i, j: 1.0) == 0.0
    assert knuth_interval_dp(0, lambda i, j: 1.0) == 0.0
    assert knuth_interval_dp(1, lambda i, j: 1.0) == 0.0


def test_divide_and_conquer_layer_agrees_with_the_naive_layer():
    rng = random.Random(19)
    for _ in range(10):
        n = rng.randrange(1, 60)
        points = sorted(rng.random() * 100 for _ in range(n))

        def cost(j, i, points=points):
            if j >= i:
                return 0.0
            span = points[i - 1] - points[j]
            return span * span

        previous = [0.0] + [rng.random() * 10 for _ in range(n)]
        expected = [
            min(previous[j] + cost(j, i) for j in range(i + 1)) for i in range(n + 1)
        ]
        assert divide_and_conquer_dp(previous, cost) == pytest.approx(expected)


def test_divide_and_conquer_over_several_layers():
    """The k-way partition problem, the canonical use of the layered form."""
    rng = random.Random(23)
    n, groups = 60, 4
    points = sorted(rng.random() * 100 for _ in range(n))

    def cost(j, i):
        if j >= i:
            return 0.0
        span = points[i - 1] - points[j]
        return span * span

    layer = [0.0] + [float("inf")] * n
    naive = layer
    for _ in range(groups):
        naive = [min(naive[j] + cost(j, i) for j in range(i + 1)) for i in range(n + 1)]
        layer = divide_and_conquer_dp(layer, cost)
    assert layer[n] == pytest.approx(naive[n])


def test_divide_and_conquer_handles_an_empty_layer():
    assert divide_and_conquer_dp([], lambda j, i: 0.0) == []
    assert divide_and_conquer_dp([0.0], lambda j, i: 0.0) == [0.0]


# --------------------------------------------------------------------------
# Visualisation
# --------------------------------------------------------------------------


def test_render_html_writes_a_self_contained_page(tmp_path):
    solution = edit_distance("kitten", "sitting").solve((6, 7))
    target = tmp_path / "trace.html"
    render_html(solution, str(target), title="Test Trace")
    text = target.read_text(encoding="utf-8")
    assert text.startswith("<!doctype html>")
    assert "Test Trace" in text
    # Everything inline: no external scripts, styles or fonts.
    assert 'src="http' not in text
    assert 'href="http' not in text
    # The trace data and the analysis summary both made it in.
    assert '"steps"' in text
    assert "critical path" in text


def test_render_html_rejects_non_grid_states(tmp_path):
    problem = DP(
        dependencies=lambda s: () if len(s) <= 1 else (s[1:],),
        combine=lambda s, vals: vals[0] + 1,
        base=lambda s: 0 if len(s) <= 1 else None,
    )
    with pytest.raises(ValueError):
        render_html(problem.solve("abc"), str(tmp_path / "x.html"))


def test_render_html_truncates_very_large_traces(tmp_path):
    solution = edit_distance("abcdefghij", "klmnopqrst").solve((10, 10))
    assert solution.state_count > 50
    target = tmp_path / "big.html"
    render_html(solution, str(target), max_steps=50)
    assert '"truncated": true' in target.read_text(encoding="utf-8")


def test_render_html_keeps_full_traces_untruncated(tmp_path):
    solution = edit_distance("ab", "cd").solve((2, 2))
    target = tmp_path / "small.html"
    render_html(solution, str(target))
    assert '"truncated": false' in target.read_text(encoding="utf-8")
