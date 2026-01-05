"""Misra-Gries Algorithm for Frequent Items (Heavy Hitters).

This module implements the Misra-Gries algorithm and the Space-Saving algorithm
to find frequent items in a data stream with bounded memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set
import heapq


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

    Optimized implementation using an offset-based strategy and bucketed counts
    to handle decrement operations in amortized constant time.
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
        # internal counters store stored_count = actual_count + offset
        self._counters: Dict[Any, int] = {}
        # buckets map stored_count -> set of items
        self._buckets: Dict[int, Set[Any]] = {}
        # min-heap of stored_counts present in buckets (may contain stale entries)
        self._heap: List[int] = []

        self.offset: int = 0
        self.total: int = 0

    def _add_to_bucket(self, item: Any, stored_count: int) -> None:
        if stored_count not in self._buckets:
            self._buckets[stored_count] = set()
            heapq.heappush(self._heap, stored_count)
            # Prune heap if it grows too large due to lazy deletion
            # This prevents memory leaks and latency spikes in long streams
            if len(self._heap) > 20 * self.k: # 20x overhead allowed before rebuild
                self._rebuild_heap()

        self._buckets[stored_count].add(item)

    def _remove_from_bucket(self, item: Any, stored_count: int) -> None:
        if stored_count in self._buckets:
            self._buckets[stored_count].discard(item)
            if not self._buckets[stored_count]:
                del self._buckets[stored_count]
                # We don't remove from heap immediately (lazy deletion)

    def _rebuild_heap(self) -> None:
        """Rebuild the heap from active bucket keys to remove stale entries."""
        self._heap = list(self._buckets.keys())
        heapq.heapify(self._heap)

    def _get_min_stored(self) -> int:
        """Return the minimum stored count currently in the map."""
        while self._heap and self._heap[0] not in self._buckets:
            heapq.heappop(self._heap)

        if not self._heap:
            return 0 # Should not happen if map not empty
        return self._heap[0]

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

        # Case 1: Item already tracked
        if item in self._counters:
            old_stored = self._counters[item]
            new_stored = old_stored + count
            self._counters[item] = new_stored

            self._remove_from_bucket(item, old_stored)
            self._add_to_bucket(item, new_stored)
            return

        # Case 2: Space available
        if len(self._counters) < self.k - 1:
            stored = count + self.offset
            self._counters[item] = stored
            self._add_to_bucket(item, stored)
            return

        # Case 3: Map full, item not tracked -> Decrement phase
        min_stored = self._get_min_stored()
        min_actual = min_stored - self.offset

        # We decrement all existing items and the new item by d
        d = min(min_actual, count)

        self.offset += d
        count -= d

        # Remove items that have effectively reached 0 (stored <= offset)
        while self._heap:
            # clean top of heap
            while self._heap and self._heap[0] not in self._buckets:
                heapq.heappop(self._heap)

            if not self._heap:
                break

            current_min = self._heap[0]
            if current_min <= self.offset:
                # Remove all items in this bucket
                items_to_remove = self._buckets[current_min]
                # We copy the set because we modify _counters
                # But we can just iterate and clear
                for it in list(items_to_remove):
                    del self._counters[it]

                del self._buckets[current_min]
                heapq.heappop(self._heap)
            else:
                break

        # If we still have count left, add the new item
        if count > 0:
            stored = count + self.offset
            self._counters[item] = stored
            self._add_to_bucket(item, stored)

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
        if item in self._counters:
            val = self._counters[item] - self.offset
            return max(0, val)
        return 0

    def approximate_counts(self) -> Dict[Any, int]:
        """Get all current approximate counts.

        Returns:
            Dict[Any, int]: Dictionary of item counts.
        """
        return {item: val - self.offset for item, val in self._counters.items()}

    @property
    def counters(self) -> Dict[Any, int]:
        """Backward compatibility property.

        Returns a COPY of the counters with adjusted values.
        Note: Modifying this dict will not affect the internal state.
        This is expensive (O(k)), so prefer approximate_counts().
        """
        return self.approximate_counts()

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

        # Build list using corrected counts
        current_counts = self.approximate_counts()

        hitters = [
            FrequentItem(item=item, estimate=count, error=0)
            for item, count in current_counts.items()
            if count >= threshold
        ]

        # If no threshold provided but we have items, return all
        if not hitters and threshold == 0 and current_counts:
            hitters = [
                FrequentItem(item=item, estimate=count, error=0)
                for item, count in current_counts.items()
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
        self.buckets: Dict[int, Set[Any]] = {}
        self.min_count: int = 0

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

        # Case 1: Item already tracked
        if item in self.counters:
            old_count = self.counters[item]
            new_count = old_count + count
            self.counters[item] = new_count

            # Remove from old bucket
            self.buckets[old_count].remove(item)
            if not self.buckets[old_count]:
                del self.buckets[old_count]

            # Add to new bucket
            if new_count not in self.buckets:
                self.buckets[new_count] = set()
            self.buckets[new_count].add(item)

            # Update min_count if needed
            if old_count == self.min_count and old_count not in self.buckets:
                while self.min_count not in self.buckets:
                    self.min_count += 1
            return

        # Case 2: New item, have space
        if len(self.counters) < self.k:
            self.counters[item] = count
            self.error[item] = 0

            if count not in self.buckets:
                self.buckets[count] = set()
            self.buckets[count].add(item)

            # Update min_count if this is the first item or smaller than current min
            if len(self.counters) == 1 or count < self.min_count:
                self.min_count = count
            return

        # Case 3: New item, no space (replace min)
        # Find an item with min_count
        if self.min_count not in self.buckets:
            # Fallback if min_count is somehow desynchronized
            if self.buckets:
                self.min_count = min(self.buckets.keys())
            else:
                self.min_count = 0

        min_set = self.buckets[self.min_count]
        min_item = min_set.pop()

        if not min_set:
            del self.buckets[self.min_count]

        del self.counters[min_item]
        del self.error[min_item]

        new_item_count = self.min_count + count
        self.counters[item] = new_item_count
        self.error[item] = self.min_count

        if new_item_count not in self.buckets:
            self.buckets[new_item_count] = set()
        self.buckets[new_item_count].add(item)

        # Update min_count if needed
        if self.min_count not in self.buckets:
            while self.min_count not in self.buckets:
                self.min_count += 1

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
