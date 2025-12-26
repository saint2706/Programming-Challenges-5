import random
import sys
from pathlib import Path

# Add the specific directory to sys.path to ensure we can import the module
# This follows the pattern mentioned in memory for nested projects
module_path = Path(__file__).parents[2] / "Algorithmic/StreamingQuantiles/python"
sys.path.append(str(module_path))

from quantiles import GKQuantile


def test_gk_quantile_basic():
    """Test basic quantile queries on a small dataset."""
    gk = GKQuantile(capacity=100)
    for i in range(100):
        gk.insert(float(i))

    # query implementation: sorted_pool[int(phi * (len - 1))]
    # len=100. idx = 0.5 * 99 = 49.5 -> int -> 49.
    # sorted_pool[49] is 49.0
    assert gk.query(0.5) == 49.0
    assert gk.query(0.0) == 0.0
    assert gk.query(1.0) == 99.0


def test_gk_quantile_reservoir_logic():
    """Test that the reservoir sampling logic works correctly for large streams."""
    random.seed(42)
    capacity = 100
    gk = GKQuantile(capacity=capacity)

    # Insert more items than capacity
    n = 1000
    for i in range(n):
        gk.insert(random.random())

    assert len(gk.pool) == capacity

    # Check that the distribution is roughly uniform (median around 0.5)
    median = gk.query(0.5)
    assert 0.4 <= median <= 0.6


def test_gk_quantile_optimization_correctness():
    """
    Test that the optimization (float check before randint) maintains correctness.
    We check this by verifying that elements are indeed replaced with probability k/n.
    """
    # This is a stochastic test, so we set a seed.
    random.seed(123)
    capacity = 10
    gk = GKQuantile(capacity=capacity)

    # Fill capacity
    for i in range(capacity):
        gk.insert(float(i))

    # Insert one more element
    # Probability of replacement should be capacity / (capacity + 1) = 10/11 ~= 0.909
    # We can't deterministicly test one insertion, but we can test many.

    replacements = 0
    trials = 1000

    for _ in range(trials):
        # Reset
        gk.n = capacity
        gk.pool = list(range(capacity))

        new_val = -1.0
        gk.insert(new_val)

        if new_val in gk.pool:
            replacements += 1

    expected_prob = capacity / (capacity + 1)
    observed_prob = replacements / trials

    # Check if observed probability is within margin of error
    assert abs(observed_prob - expected_prob) < 0.05
