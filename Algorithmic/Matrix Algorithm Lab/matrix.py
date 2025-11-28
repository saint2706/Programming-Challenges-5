"""
Matrix implementation supporting list-of-lists or NumPy backends.

Features:
    - Addition and subtraction
    - Naive matrix multiplication
    - Strassen recursive multiplication with zero padding to powers of two
    - Determinant and inverse helpers (powered by NumPy)
    - Benchmark helper to compare naive, Strassen, and NumPy performance
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

# Type alias for numbers in the matrix
Number = Union[float, int]


def _ensure_rectangular(data: Sequence[Sequence[Number]]) -> None:
    """Validate that the input data forms a rectangular matrix.

    Args:
        data: A sequence of sequences (rows).

    Raises:
        ValueError: If the data is empty or rows have inconsistent lengths.
    """
    if not data:
        raise ValueError("Matrix data cannot be empty")
    row_length = len(data[0])
    for row in data:
        if len(row) != row_length:
            raise ValueError("All rows must have the same length")


def _next_power_of_two(n: int) -> int:
    """Calculate the next power of two greater than or equal to n.

    Args:
        n: The input integer.

    Returns:
        int: The next power of two.
    """
    return 1 if n == 0 else 1 << (n - 1).bit_length()


@dataclass
class Matrix:
    """A Matrix class supporting multiple backends and algorithms.

    Attributes:
        data: The underlying data, either a list of lists or a NumPy array.
        backend: The backend storage to use ('list' or 'numpy').
    """

    data: Union[List[List[Number]], np.ndarray]
    backend: str = "list"

    def __post_init__(self) -> None:
        """Validate backend and normalize data format."""
        if self.backend not in {"list", "numpy"}:
            raise ValueError("Backend must be either 'list' or 'numpy'")

        if self.backend == "list":
            if not isinstance(self.data, list):
                # Convert numpy array or other iterable to list of lists
                # Type ignore: Assuming input is convertible
                self.data = [list(row) for row in self.data]  # type: ignore
            _ensure_rectangular(self.data)  # type: ignore[arg-type]
        else:
            self.data = np.array(self.data, dtype=float)

    @property
    def shape(self) -> Tuple[int, int]:
        """Get the dimensions of the matrix (rows, cols)."""
        if self.backend == "list":
            # Type ignore: validation ensures data is List[List[Number]]
            return len(self.data), len(self.data[0])  # type: ignore
        # NumPy shape returns tuple
        return int(self.data.shape[0]), int(self.data.shape[1])  # type: ignore

    def as_array(self) -> np.ndarray:
        """Convert the matrix to a NumPy array."""
        return np.array(self.data, dtype=float)

    def to_list(self) -> List[List[float]]:
        """Convert the matrix to a standard Python list of lists."""
        return self.as_array().tolist()

    def _return(self, array: np.ndarray) -> "Matrix":
        """Helper to return a new Matrix instance in the same backend."""
        if self.backend == "list":
            return Matrix(array.tolist(), backend="list")
        return Matrix(array, backend="numpy")

    def add(self, other: "Matrix") -> "Matrix":
        """Add another matrix to this one.

        Args:
            other: The matrix to add.

        Returns:
            Matrix: The result of the addition.

        Raises:
            ValueError: If shapes do not match.
        """
        if self.shape != other.shape:
            raise ValueError("Shapes must match for addition")
        if self.backend == "list":
            # Type ignore: list backend guarantees List[List] structure
            result = [
                [a + b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self.data, other.data)  # type: ignore
            ]
            return Matrix(result, backend="list")
        return Matrix(self.data + other.data, backend="numpy")  # type: ignore

    def subtract(self, other: "Matrix") -> "Matrix":
        """Subtract another matrix from this one.

        Args:
            other: The matrix to subtract.

        Returns:
            Matrix: The result of the subtraction.

        Raises:
            ValueError: If shapes do not match.
        """
        if self.shape != other.shape:
            raise ValueError("Shapes must match for subtraction")
        if self.backend == "list":
            result = [
                [a - b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self.data, other.data)  # type: ignore
            ]
            return Matrix(result, backend="list")
        return Matrix(self.data - other.data, backend="numpy")  # type: ignore

    def naive_multiply(self, other: "Matrix") -> "Matrix":
        """Multiply matrices using the standard O(N^3) algorithm.

        Args:
            other: The multiplier matrix.

        Returns:
            Matrix: The product matrix.

        Raises:
            ValueError: If inner dimensions do not match (cols_a != rows_b).
        """
        rows_a, cols_a = self.shape
        rows_b, cols_b = other.shape
        if cols_a != rows_b:
            raise ValueError("Inner dimensions must match for multiplication")

        if self.backend == "list":
            # Initialize result with zeros
            result: List[List[float]] = [
                [0.0 for _ in range(cols_b)] for _ in range(rows_a)
            ]
            # data is guaranteed to be List[List] here
            data_a: List[List[Number]] = self.data  # type: ignore
            data_b: List[List[Number]] = other.data  # type: ignore

            for i in range(rows_a):
                for k in range(cols_a):
                    val_a = float(data_a[i][k])
                    # optimization: skip zero
                    if val_a == 0:
                        continue
                    for j in range(cols_b):
                        result[i][j] += val_a * float(data_b[k][j])
            return Matrix(result, backend="list")

        # NumPy backend
        product = np.dot(self.data, other.data)
        return Matrix(product, backend="numpy")

    def strassen_multiply(self, other: "Matrix", threshold: int = 64) -> "Matrix":
        """Multiply matrices using Strassen's Algorithm (Divide & Conquer).

        Strassen's algorithm reduces the number of recursive multiplications
        from 8 to 7, achieving O(N^log2(7)) approx O(N^2.81).

        Args:
            other: The multiplier matrix.
            threshold: Size below which to switch to standard multiplication.

        Returns:
            Matrix: The product matrix.

        Raises:
            ValueError: If inner dimensions do not match.
        """
        a = self.as_array()
        b = other.as_array()
        rows_a, cols_a = a.shape
        rows_b, cols_b = b.shape
        if cols_a != rows_b:
            raise ValueError("Inner dimensions must match for multiplication")

        # Pad to next power of two for clean splitting
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

            # 7 recursive calls
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
        # Crop result to original dimensions
        trimmed = padded_result[:rows_a, :cols_b]
        return self._return(trimmed)

    def determinant(self) -> float:
        """Calculate the determinant of the matrix.

        Returns:
            float: The determinant.

        Raises:
            ValueError: If the matrix is not square.
        """
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("Determinant is defined only for square matrices")
        return float(np.linalg.det(self.as_array()))

    def inverse(self) -> "Matrix":
        """Calculate the multiplicative inverse of the matrix.

        Returns:
            Matrix: The inverse matrix.

        Raises:
            ValueError: If the matrix is not square or is singular.
        """
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
        seed: Optional[int] = None,
    ) -> "Matrix":
        """Generate a random matrix.

        Args:
            rows: Number of rows.
            cols: Number of columns.
            backend: Backend to use.
            low: Lower bound for random values.
            high: Upper bound for random values.
            seed: Random seed for reproducibility.

        Returns:
            Matrix: A new random matrix.
        """
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
) -> List[Dict[str, Union[int, float]]]:
    """Benchmark naive, Strassen, and NumPy multiplication for given sizes.

    Args:
        sizes: List of dimension sizes (N for NxN matrices) to test.
        backend: Backend to use for Matrix objects.
        repeats: Number of times to repeat each test for averaging.
        threshold: Strassen recursion base case threshold.
        seed: Random seed.

    Returns:
        List[dict]: List of dictionaries containing timing results.
    """

    rng = np.random.default_rng(seed)
    results: List[Dict[str, Union[int, float]]] = []

    for n in sizes:
        a_data = rng.uniform(-1, 1, size=(n, n))
        b_data = rng.uniform(-1, 1, size=(n, n))
        # Construct matrices based on backend preference
        a = Matrix(a_data.tolist() if backend == "list" else a_data, backend=backend)
        b = Matrix(b_data.tolist() if backend == "list" else b_data, backend=backend)

        timings: Dict[str, Union[int, float]] = {}

        # Test custom implementations
        methods = {
            "naive": Matrix.naive_multiply,
            "strassen": lambda self, other: self.strassen_multiply(
                other, threshold=threshold
            ),
        }

        for label, func in methods.items():
            elapsed = []
            for _ in range(repeats):
                start = time.perf_counter()
                func(a, b)
                elapsed.append(time.perf_counter() - start)
            timings[label] = sum(elapsed) / repeats

        # Test native NumPy as baseline
        numpy_times: List[float] = []
        arr_a, arr_b = a.as_array(), b.as_array()
        for _ in range(repeats):
            start = time.perf_counter()
            _ = arr_a @ arr_b
            numpy_times.append(time.perf_counter() - start)
        timings["numpy"] = sum(numpy_times) / repeats

        results.append({"size": n, **timings})

    return results
