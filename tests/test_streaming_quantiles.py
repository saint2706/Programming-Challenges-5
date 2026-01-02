import random
import sys
from pathlib import Path

# Add the specific directory to sys.path to ensure we can import the module
# This follows the pattern mentioned in memory for nested projects
module_path = Path(__file__).parent.parent / "Algorithmic/StreamingQuantiles/python"
sys.path.insert(0, str(module_path))

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


def test_gk_quantile_interleaved_query_insert():
    """
    Test correctness for interleaved query/insert workloads.
    This validates the in-place sort optimization: the pool remains nearly-sorted
    between queries, and Timsort efficiently handles insertions that slightly perturb order.
    Pattern: insert batch → query → insert more → query → repeat.
    """
    random.seed(789)
    capacity = 50
    gk = GKQuantile(capacity=capacity)
    
    # Phase 1: Insert initial batch
    for i in range(30):
        gk.insert(float(i))
    
    # Query 1: Should get median around 14.5
    median1 = gk.query(0.5)
    assert 13.0 <= median1 <= 16.0, f"Expected median ~14.5, got {median1}"
    
    # Phase 2: Insert more values
    for i in range(30, 60):
        gk.insert(float(i))
    
    # Query 2: Should get median around 29.5
    median2 = gk.query(0.5)
    assert 27.0 <= median2 <= 32.0, f"Expected median ~29.5, got {median2}"
    
    # Phase 3: Insert values that will partially replace existing pool
    for i in range(60, 120):
        gk.insert(float(i))
    
    # Query 3: After many insertions beyond capacity, median should shift higher
    median3 = gk.query(0.5)
    # With reservoir sampling, we expect a mix of old and new values
    # The median should be somewhere between the early values and late values
    assert median3 > median2, f"Expected median to increase, but {median3} <= {median2}"
    
    # Phase 4: Multiple queries without inserts should give consistent results
    q1 = gk.query(0.25)
    q2 = gk.query(0.5)
    q3 = gk.query(0.75)
    
    # Verify ordering: 25th percentile < median < 75th percentile
    assert q1 < q2 < q3, f"Expected {q1} < {q2} < {q3}"
    
    # Phase 5: Insert more and query again
    for i in range(120, 150):
        gk.insert(float(i))
    
    final_median = gk.query(0.5)
    # Pool size should remain at capacity
    assert len(gk.pool) == capacity
    # Final median should be reasonable given the data distribution
    assert 0 <= final_median <= 150
