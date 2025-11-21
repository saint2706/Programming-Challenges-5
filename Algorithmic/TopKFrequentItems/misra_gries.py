from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class FrequentItem:
    item: Any
    estimate: int
    error: int = 0


class MisraGriesCounter:
    """Misra-Gries heavy hitter counter.

    Maintains at most ``k - 1`` counters and returns approximate frequencies
    for items appearing frequently in a stream.
    """

    def __init__(self, k: int) -> None:
        if k < 2:
            raise ValueError("k must be at least 2 for Misra-Gries")
        self.k = k
        self.counters: Dict[Any, int] = {}
        self.total: int = 0

    def update(self, item: Any, count: int = 1) -> None:
        if count <= 0:
            raise ValueError("count must be positive")
        self.total += count
        remaining = count
        while remaining > 0:
            if item in self.counters:
                self.counters[item] += remaining
                break
            if len(self.counters) < self.k - 1:
                self.counters[item] = remaining
                break

            keys_to_delete = []
            for key in list(self.counters.keys()):
                self.counters[key] -= 1
                if self.counters[key] == 0:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self.counters[key]
            remaining -= 1

    def bulk_update(self, items: Iterable[Any]) -> None:
        for item in items:
            self.update(item)

    def query(self, item: Any) -> int:
        return self.counters.get(item, 0)

    def approximate_counts(self) -> Dict[Any, int]:
        return dict(self.counters)

    def heavy_hitters(
        self, *, min_fraction: float | None = None, min_count: int | None = None
    ) -> List[FrequentItem]:
        threshold = min_count or 0
        if min_fraction is not None:
            threshold = max(threshold, int(min_fraction * self.total))

        hitters = [
            FrequentItem(item=item, estimate=count, error=0)
            for item, count in self.counters.items()
            if count >= threshold
        ]
        if not hitters and threshold > 0:
            hitters = [
                FrequentItem(item=item, estimate=count, error=0)
                for item, count in self.counters.items()
            ]
        hitters.sort(key=lambda fi: fi.estimate, reverse=True)
        return hitters


class SpaceSavingCounter:
    """Space-Saving heavy hitter counter.

    Keeps ``k`` slots and replaces the minimum counter when a new item arrives.
    The ``error`` field tracks the overestimation bound for each stored item.
    """

    def __init__(self, k: int) -> None:
        if k < 1:
            raise ValueError("k must be at least 1 for Space-Saving")
        self.k = k
        self.counters: Dict[Any, int] = {}
        self.error: Dict[Any, int] = {}
        self.total: int = 0

    def update(self, item: Any, count: int = 1) -> None:
        if count <= 0:
            raise ValueError("count must be positive")
        self.total += count

        if item in self.counters:
            self.counters[item] += count
            return
        if len(self.counters) < self.k:
            self.counters[item] = count
            self.error[item] = 0
            return

        # Replace the minimum counter
        min_item = min(self.counters, key=self.counters.get)
        min_count = self.counters[min_item]
        del self.counters[min_item]
        del self.error[min_item]

        self.counters[item] = min_count + count
        self.error[item] = min_count

    def bulk_update(self, items: Iterable[Any]) -> None:
        for item in items:
            self.update(item)

    def query(self, item: Any) -> FrequentItem | None:
        if item not in self.counters:
            return None
        return FrequentItem(
            item=item, estimate=self.counters[item], error=self.error[item]
        )

    def approximate_counts(self) -> Dict[Any, FrequentItem]:
        return {
            item: FrequentItem(item=item, estimate=count, error=self.error[item])
            for item, count in self.counters.items()
        }

    def heavy_hitters(
        self, *, min_fraction: float | None = None, min_count: int | None = None
    ) -> List[FrequentItem]:
        threshold = min_count or 0
        if min_fraction is not None:
            threshold = max(threshold, int(min_fraction * self.total))

        hitters = [
            FrequentItem(item=item, estimate=count, error=self.error[item])
            for item, count in self.counters.items()
            if count >= threshold
        ]
        hitters.sort(key=lambda fi: fi.estimate, reverse=True)
        return hitters
