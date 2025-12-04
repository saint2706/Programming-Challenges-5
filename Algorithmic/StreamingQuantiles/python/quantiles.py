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
            # Reservoir logic: replace element with prob capacity/n
            j = random.randint(0, self.n - 1)
            if j < self.capacity:
                self.pool[j] = v

    def query(self, phi: float) -> float:
        if not self.pool:
            return 0.0
        # Sort pool to find quantile
        sorted_pool = sorted(self.pool)
        idx = int(phi * (len(sorted_pool) - 1))
        return sorted_pool[idx]
