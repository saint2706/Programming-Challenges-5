"""Misra-Gries Algorithm for Frequent Items (Heavy Hitters).

This module implements the Misra-Gries algorithm and the Space-Saving algorithm
to find frequent items in a data stream with bounded memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class FrequentItem:
    """A data class representing a potentially frequent item.

    Attributes:
        item: The item identifier.
        estimate: The estimated frequency count.
        error: The maximum possible overestimation error (0 for Misra-Gries).
    """

    item: Any
    estimate: int
    error: int = 0


class MisraGriesCounter:
    """Misra-Gries heavy hitter counter.

    Maintains at most ``k - 1`` counters and returns approximate frequencies
    for items appearing frequently in a stream.
    """

    def __init__(self, k: int) -> None:
        """Initialize the Misra-Gries counter.

        Args:
            k: The number of counters to maintain. Guarantees finding items
               with frequency > N/k.

        Raises:
            ValueError: If k < 2.
        """
        if k < 2:
            raise ValueError("k must be at least 2 for Misra-Gries")
        self.k = k
        self.counters: Dict[Any, int] = {}
        self.total: int = 0

    def update(self, item: Any, count: int = 1) -> None:
        """Update the counter with an item.

        Args:
            item: The item from the stream.
            count: The number of times the item appears (default 1).

        Raises:
            ValueError: If count <= 0.
        """
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

            # Decrement all counters
            keys_to_delete = []
            for key in list(self.counters.keys()):
                self.counters[key] -= 1
                if self.counters[key] == 0:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self.counters[key]
            remaining -= 1

    def bulk_update(self, items: Iterable[Any]) -> None:
        """Update with a batch of items.

        Args:
            items: An iterable of items.
        """
        for item in items:
            self.update(item)

    def query(self, item: Any) -> int:
        """Query the estimated count of an item.

        Args:
            item: The item to query.

        Returns:
            int: Estimated count.
        """
        return self.counters.get(item, 0)

    def approximate_counts(self) -> Dict[Any, int]:
        """Get all current approximate counts.

        Returns:
            Dict[Any, int]: Dictionary of item counts.
        """
        return dict(self.counters)

    def heavy_hitters(
        self,
        *,
        min_fraction: Optional[float] = None,
        min_count: Optional[int] = None,
    ) -> List[FrequentItem]:
        """Retrieve identified heavy hitters exceeding a threshold.

        Args:
            min_fraction: Minimum frequency fraction (0.0 to 1.0).
            min_count: Minimum absolute count.

        Returns:
            List[FrequentItem]: List of frequent items sorted by estimate.
        """
        threshold = min_count or 0
        if min_fraction is not None:
            threshold = max(threshold, int(min_fraction * self.total))

        hitters = [
            FrequentItem(item=item, estimate=count, error=0)
            for item, count in self.counters.items()
            if count >= threshold
        ]
        # If no threshold provided but we have items, return all
        if not hitters and threshold == 0 and self.counters:
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
        """Initialize the Space-Saving counter.

        Args:
            k: Number of counters.

        Raises:
            ValueError: If k < 1.
        """
        if k < 1:
            raise ValueError("k must be at least 1 for Space-Saving")
        self.k = k
        self.counters: Dict[Any, int] = {}
        self.error: Dict[Any, int] = {}
        self.total: int = 0

    def update(self, item: Any, count: int = 1) -> None:
        """Update the counter with an item.

        Args:
            item: The item from the stream.
            count: The number of times the item appears.

        Raises:
            ValueError: If count <= 0.
        """
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
        min_item = min(self.counters, key=self.counters.get)  # type: ignore
        min_count = self.counters[min_item]
        del self.counters[min_item]
        del self.error[min_item]

        self.counters[item] = min_count + count
        self.error[item] = min_count

    def bulk_update(self, items: Iterable[Any]) -> None:
        """Update with a batch of items.

        Args:
            items: An iterable of items.
        """
        for item in items:
            self.update(item)

    def query(self, item: Any) -> Optional[FrequentItem]:
        """Query for a specific item.

        Args:
            item: The item to look up.

        Returns:
            Optional[FrequentItem]: Item stats if tracked, else None.
        """
        if item not in self.counters:
            return None
        return FrequentItem(
            item=item, estimate=self.counters[item], error=self.error[item]
        )

    def approximate_counts(self) -> Dict[Any, FrequentItem]:
        """Get all current items with their stats.

        Returns:
            Dict[Any, FrequentItem]: Map of item to FrequentItem stats.
        """
        return {
            item: FrequentItem(item=item, estimate=count, error=self.error[item])
            for item, count in self.counters.items()
        }

    def heavy_hitters(
        self,
        *,
        min_fraction: Optional[float] = None,
        min_count: Optional[int] = None,
    ) -> List[FrequentItem]:
        """Retrieve identified heavy hitters exceeding a threshold.

        Args:
            min_fraction: Minimum frequency fraction.
            min_count: Minimum absolute count.

        Returns:
            List[FrequentItem]: List of frequent items sorted by estimate.
        """
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
