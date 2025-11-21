"""
Matrix implementation supporting list-of-lists or NumPy backends.

Features
--------
- Addition and subtraction
- Naive matrix multiplication
- Strassen recursive multiplication with zero padding to powers of two
- Determinant and inverse helpers (powered by NumPy)
- Benchmark helper to compare naive, Strassen, and NumPy performance
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np

Number = float | int


def _ensure_rectangular(data: Sequence[Sequence[Number]]) -> None:
    if not data:
        raise ValueError("Matrix data cannot be empty")
    row_length = len(data[0])
    for row in data:
        if len(row) != row_length:
            raise ValueError("All rows must have the same length")


def _next_power_of_two(n: int) -> int:
    return 1 if n == 0 else 1 << (n - 1).bit_length()


@dataclass
class Matrix:
    data: List[List[Number]] | np.ndarray
    backend: str = "list"

    def __post_init__(self) -> None:
        if self.backend not in {"list", "numpy"}:
            raise ValueError("Backend must be either 'list' or 'numpy'")

        if self.backend == "list":
            if not isinstance(self.data, list):
                self.data = [list(row) for row in self.data]  # type: ignore[assignment]
            _ensure_rectangular(self.data)  # type: ignore[arg-type]
        else:
            self.data = np.array(self.data, dtype=float)

    @property
    def shape(self) -> tuple[int, int]:
        if self.backend == "list":
            return len(self.data), len(self.data[0])
        return int(self.data.shape[0]), int(self.data.shape[1])

    def as_array(self) -> np.ndarray:
        return np.array(self.data, dtype=float)

    def to_list(self) -> List[List[float]]:
        return self.as_array().tolist()

    def _return(self, array: np.ndarray) -> "Matrix":
        if self.backend == "list":
            return Matrix(array.tolist(), backend="list")
        return Matrix(array, backend="numpy")

    def add(self, other: "Matrix") -> "Matrix":
        if self.shape != other.shape:
            raise ValueError("Shapes must match for addition")
        if self.backend == "list":
            result = [
                [a + b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self.data, other.data)
            ]
            return Matrix(result, backend="list")
        return Matrix(self.data + other.data, backend="numpy")

    def subtract(self, other: "Matrix") -> "Matrix":
        if self.shape != other.shape:
            raise ValueError("Shapes must match for subtraction")
        if self.backend == "list":
            result = [
                [a - b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self.data, other.data)
            ]
            return Matrix(result, backend="list")
        return Matrix(self.data - other.data, backend="numpy")

    def naive_multiply(self, other: "Matrix") -> "Matrix":
        rows_a, cols_a = self.shape
        rows_b, cols_b = other.shape
        if cols_a != rows_b:
            raise ValueError("Inner dimensions must match for multiplication")

        if self.backend == "list":
            result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
            for i in range(rows_a):
                for k in range(cols_a):
                    for j in range(cols_b):
                        result[i][j] += float(self.data[i][k]) * float(other.data[k][j])
            return Matrix(result, backend="list")

        product = np.dot(self.data, other.data)
        return Matrix(product, backend="numpy")

    def strassen_multiply(self, other: "Matrix", threshold: int = 64) -> "Matrix":
        a = self.as_array()
        b = other.as_array()
        rows_a, cols_a = a.shape
        rows_b, cols_b = b.shape
        if cols_a != rows_b:
            raise ValueError("Inner dimensions must match for multiplication")

        size = _next_power_of_two(max(rows_a, cols_a, rows_b, cols_b))
        padded_a = np.zeros((size, size))
        padded_b = np.zeros((size, size))
        padded_a[:rows_a, :cols_a] = a
        padded_b[:rows_b, :cols_b] = b

        def strassen(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            n = x.shape[0]
            if n <= threshold:
                return x @ y

            k = n // 2
            a11, a12, a21, a22 = x[:k, :k], x[:k, k:], x[k:, :k], x[k:, k:]
            b11, b12, b21, b22 = y[:k, :k], y[:k, k:], y[k:, :k], y[k:, k:]

            m1 = strassen(a11 + a22, b11 + b22)
            m2 = strassen(a21 + a22, b11)
            m3 = strassen(a11, b12 - b22)
            m4 = strassen(a22, b21 - b11)
            m5 = strassen(a11 + a12, b22)
            m6 = strassen(a21 - a11, b11 + b12)
            m7 = strassen(a12 - a22, b21 + b22)

            c11 = m1 + m4 - m5 + m7
            c12 = m3 + m5
            c21 = m2 + m4
            c22 = m1 - m2 + m3 + m6

            top = np.hstack((c11, c12))
            bottom = np.hstack((c21, c22))
            return np.vstack((top, bottom))

        padded_result = strassen(padded_a, padded_b)
        trimmed = padded_result[:rows_a, :cols_b]
        return self._return(trimmed)

    def determinant(self) -> float:
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("Determinant is defined only for square matrices")
        return float(np.linalg.det(self.as_array()))

    def inverse(self) -> "Matrix":
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("Inverse is defined only for square matrices")
        inv = np.linalg.inv(self.as_array())
        return self._return(inv)

    @classmethod
    def random(
        cls,
        rows: int,
        cols: int,
        backend: str = "numpy",
        low: float = -10.0,
        high: float = 10.0,
        seed: int | None = None,
    ) -> "Matrix":
        rng = np.random.default_rng(seed)
        data = rng.uniform(low, high, size=(rows, cols))
        if backend == "list":
            return cls(data.tolist(), backend="list")
        return cls(data, backend="numpy")


def benchmark_multiplication(
    sizes: Iterable[int],
    backend: str = "numpy",
    repeats: int = 3,
    threshold: int = 64,
    seed: int = 0,
) -> List[dict]:
    """Benchmark naive, Strassen, and NumPy multiplication for given sizes.

    Returns a list of dictionaries with timings in seconds.
    """

    rng = np.random.default_rng(seed)
    results: List[dict] = []

    for n in sizes:
        a_data = rng.uniform(-1, 1, size=(n, n))
        b_data = rng.uniform(-1, 1, size=(n, n))
        a = Matrix(a_data.tolist() if backend == "list" else a_data, backend=backend)
        b = Matrix(b_data.tolist() if backend == "list" else b_data, backend=backend)

        timings = {}
        for label, func in {
            "naive": Matrix.naive_multiply,
            "strassen": lambda self, other: self.strassen_multiply(
                other, threshold=threshold
            ),
        }.items():
            elapsed = []
            for _ in range(repeats):
                start = time.perf_counter()
                func(a, b)
                elapsed.append(time.perf_counter() - start)
            timings[label] = sum(elapsed) / repeats

        numpy_times: list[float] = []
        for _ in range(repeats):
            start = time.perf_counter()
            _ = a.as_array() @ b.as_array()
            numpy_times.append(time.perf_counter() - start)
        timings["numpy"] = sum(numpy_times) / repeats

        results.append({"size": n, **timings})

    return results
