"""
Implementation of the algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import statistics
import time
from typing import Callable, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class QuickselectResult:
    """Result of a quickselect benchmark run."""

    value: T
    iterations: int
    average_time: float


def _partition(values: List[T], left: int, right: int, pivot_index: int, key: Callable[[T], T]) -> int:
    """
    Docstring for _partition.
    """
    pivot_value = key(values[pivot_index])
    values[pivot_index], values[right] = values[right], values[pivot_index]
    store_index = left
    for i in range(left, right):
        if key(values[i]) < pivot_value:
            values[store_index], values[i] = values[i], values[store_index]
            store_index += 1
    values[right], values[store_index] = values[store_index], values[right]
    return store_index


def quickselect(values: List[T], k: int, *, key: Optional[Callable[[T], T]] = None, rng: Optional[random.Random] = None) -> T:
    """Select the k-th smallest element in-place using randomized partitioning."""

    if not 0 <= k < len(values):
        raise IndexError("k is out of bounds")

    key = key or (lambda x: x)
    rng = rng or random

    left, right = 0, len(values) - 1
    while True:
        if left == right:
            return values[left]

        pivot_index = rng.randint(left, right)
        pivot_index = _partition(values, left, right, pivot_index, key)

        if k == pivot_index:
            return values[k]
        if k < pivot_index:
            right = pivot_index - 1
        else:
            left = pivot_index + 1


def benchmark_quickselect(
    trials: int,
    size: int,
    *,
    k: Optional[int] = None,
    rng: Optional[random.Random] = None,
) -> QuickselectResult:
    """Run multiple quickselect trials and report average execution time."""

    rng = rng or random.Random()
    times: List[float] = []
    target_index = k if k is not None else size // 2

    for _ in range(trials):
        items = [rng.randint(0, size * 10) for _ in range(size)]
        start = time.perf_counter()
        value = quickselect(items, target_index, rng=rng)
        times.append(time.perf_counter() - start)
        assert value == sorted(items)[target_index]

    return QuickselectResult(value=value, iterations=trials, average_time=statistics.mean(times))
