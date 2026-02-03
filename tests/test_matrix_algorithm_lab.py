import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Algorithmic.MatrixAlgorithmLab import (  # noqa: E402
    Matrix,
    benchmark_multiplication,
)


def test_addition_and_subtraction():
    a = Matrix.random(3, 4, backend="numpy", seed=1)
    b = Matrix.random(3, 4, backend="numpy", seed=2)

    added = a.add(b).as_array()
    subtracted = a.subtract(b).as_array()

    assert np.allclose(added, a.as_array() + b.as_array())
    assert np.allclose(subtracted, a.as_array() - b.as_array())


def test_naive_multiplication_matches_numpy():
    a = Matrix.random(3, 2, backend="list", seed=0)
    b = Matrix.random(2, 4, backend="list", seed=1)

    product = a.naive_multiply(b).as_array()
    expected = np.array(a.data) @ np.array(b.data)

    assert np.allclose(product, expected)


def test_strassen_padding_and_correctness():
    a = Matrix.random(3, 3, backend="numpy", seed=3)
    b = Matrix.random(3, 3, backend="numpy", seed=4)

    result = a.strassen_multiply(b, threshold=1).as_array()
    expected = a.as_array() @ b.as_array()

    assert np.allclose(result, expected)


def test_determinant_and_inverse_round_trip():
    # Create a well-conditioned 3x3 matrix
    a = Matrix(
        [
            [4.0, 2.0, 1.0],
            [0.0, 3.0, -1.0],
            [2.0, -2.0, 5.0],
        ],
        backend="list",
    )

    det = a.determinant()
    inv = a.inverse().as_array()

    assert abs(det) > 0.1
    identity = a.as_array() @ inv
    assert np.allclose(identity, np.eye(3))


def test_benchmark_returns_timings():
    results = benchmark_multiplication(sizes=[2, 4], backend="list", repeats=1, seed=42)
    assert len(results) == 2
    for entry in results:
        assert set(entry.keys()) == {"size", "naive", "strassen", "numpy"}
        assert entry["size"] in {2, 4}
        assert entry["naive"] >= 0
        assert entry["strassen"] >= 0
        assert entry["numpy"] >= 0
