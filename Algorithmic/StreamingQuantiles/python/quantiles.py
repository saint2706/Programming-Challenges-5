"""Streaming Quantiles using Reservoir Sampling.

For small datasets, keeps exact values. For large streams, maintains a uniform random sample.
"""

import random
from typing import List


class GKQuantile:
    """Reservoir Sampling based Quantile Estimator."""

    def __init__(self, epsilon: float = 0.01, capacity: int = 1000):
        self.capacity = capacity
        self.pool: List[float] = []
        self.n = 0

    def insert(self, v: float):
        self.n += 1
        if len(self.pool) < self.capacity:
            self.pool.append(v)
        else:
            # Reservoir sampling: replace element with probability capacity/n
            if random.random() < self.capacity / self.n:
                j = random.randint(0, self.capacity - 1)
                self.pool[j] = v

    def query(self, phi: float) -> float:
        if not self.pool:
            return 0.0
        # Sort pool in-place to find quantile.
        # This is significantly faster than sorted(self.pool) for interleaved
        # query/insert workloads because Timsort is efficient on nearly-sorted data.
        # Since reservoir sampling eviction is based on random indices (not values),
        # changing the order of elements in the pool does not affect the statistical properties.
        self.pool.sort()
        idx = int(phi * (len(self.pool) - 1))
        return self.pool[idx]
