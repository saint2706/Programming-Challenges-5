import math
import pathlib
import sys

# Ensure repository root is on the import path when pytest changes cwd.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from approximate_set_membership.bloom import (
    BitArray,
    benchmark_dataset,
    run_false_positive_experiment,
)


def test_bitarray_set_and_get():
    bits = BitArray(32)
    bits.set(0)
    bits.set(31)

    assert bits.get(0) is True
    assert bits.get(31) is True
    assert bits.get(1) is False
    assert math.isclose(bits.density(), 2 / 32)


def test_false_positive_rate_matches_theory():
    result = run_false_positive_experiment(
        filter_size=20_000,
        hash_count=7,
        insertions=4_000,
        queries=5_000,
        seed=42,
    )

    difference = abs(result.measured_fpr - result.theoretical_fpr)
    assert difference < 0.02


def test_benchmark_on_dataset_runs_and_reports_reasonable_rates():
    dataset = [f"word-{i}" for i in range(5_000)]
    result = benchmark_dataset(dataset, false_positive_rate=0.02)

    assert result.inserted == len(dataset)
    assert result.queried == len(dataset)
    assert 0 <= result.measured_fpr <= 0.1
    assert math.isclose(result.theoretical_fpr, 0.02, rel_tol=0.35)
