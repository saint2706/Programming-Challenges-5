"""Weighted Interval Scheduling implementation using Dynamic Programming.

This module solves the Weighted Interval Scheduling problem: given a set of intervals
where each interval has a start time, end time, and a weight (value), find the
subset of non-overlapping intervals that maximizes the total weight.

Time Complexity: O(n log n) due to sorting.
Space Complexity: O(n) for storing DP table and predecessors.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Union


@dataclass(frozen=True, order=True)
class Interval:
    """Data model representing an interval with a weight.

    Attributes:
        start (int): Start time of the interval.
        end (int): End time of the interval.
        weight (int): Weight/value associated with the interval.
    """

    sort_index: Tuple[int, int, int] = field(init=False, repr=False)
    start: int = field(compare=False)
    end: int = field(compare=False)
    weight: int = field(compare=False)

    def __post_init__(self) -> None:
        """Set sort_index for default ordering (by end time)."""
        # Sort primarily by end time to optimize the scheduler
        object.__setattr__(self, "sort_index", (self.end, self.start, self.weight))

    def as_tuple(self) -> Tuple[int, int, int]:
        """Return the interval as a (start, end, weight) tuple.

        Returns:
            Tuple[int, int, int]: The interval data.
        """
        return (self.start, self.end, self.weight)


class AdvancedIntervalScheduler:
    """Weighted interval scheduling using dynamic programming."""

    def __init__(
        self, intervals: Iterable[Union[Tuple[int, int, int], Interval]]
    ) -> None:
        """Initialize the scheduler with interval data.

        Args:
            intervals: Iterable of (start, end, weight) tuples or Interval objects.
        """
        self.intervals: List[Interval] = [
            (
                interval
                if isinstance(interval, Interval)
                else Interval(start=interval[0], end=interval[1], weight=interval[2])
            )
            for interval in intervals
        ]
        self.n = len(self.intervals)

    def find_optimal_schedule(self) -> Tuple[int, List[Interval]]:
        """Compute the maximum weight subset of non-overlapping intervals.

        Returns:
            Tuple[int, List[Interval]]: A tuple containing:
                - The maximum total weight found.
                - A list of the selected intervals in the optimal schedule.
        """
        if not self.intervals:
            return 0, []

        # 1. Sort intervals by finish time
        sorted_intervals = sorted(self.intervals)
        end_times = [interval.end for interval in sorted_intervals]

        # 2. Compute p[j] for each interval j
        # p[j] is the index of the rightmost interval compatible with j
        p = self._compute_predecessors(sorted_intervals, end_times)

        # 3. Compute OPT values using DP
        # dp[j] stores the max weight using subset of first j intervals
        dp = [0] * (self.n + 1)

        for j in range(1, self.n + 1):
            interval = sorted_intervals[j - 1]
            # Option 1: Include interval j. Add its weight + OPT(p[j])
            include_weight = interval.weight + dp[p[j - 1] + 1]
            # Option 2: Exclude interval j. Weight is OPT(j-1)
            exclude_weight = dp[j - 1]
            dp[j] = max(include_weight, exclude_weight)

        # 4. Backtrack to find the solution
        selected = self._backtrack_schedule(dp, p, sorted_intervals)
        return dp[self.n], selected

    def _compute_predecessors(
        self, intervals: Sequence[Interval], end_times: Sequence[int]
    ) -> List[int]:
        """Compute the predecessor array p.

        For each interval j, p[j] is the largest index i < j such that
        interval i is compatible with interval j (i.e., i.end <= j.start).

        Args:
            intervals: List of sorted intervals.
            end_times: List of end times for binary search.

        Returns:
            List[int]: List of indices. -1 indicates no compatible predecessor.
        """
        p = [-1] * self.n
        for j, interval in enumerate(intervals):
            # Find rightmost interval that ends <= current.start
            # bisect_right returns insertion point to maintain order
            i = bisect.bisect_right(end_times, interval.start, hi=j) - 1
            p[j] = i if i >= 0 else -1
        return p

    def _backtrack_schedule(
        self, dp: Sequence[int], p: Sequence[int], intervals: Sequence[Interval]
    ) -> List[Interval]:
        """Reconstruct the chosen intervals from the DP table.

        Args:
            dp: The dynamic programming table.
            p: The predecessor array.
            intervals: The list of sorted intervals.

        Returns:
            List[Interval]: The list of intervals in the optimal solution.
        """
        selected: List[Interval] = []
        j = self.n
        while j > 0:
            interval = intervals[j - 1]
            include_weight = interval.weight + dp[p[j - 1] + 1]
            if include_weight >= dp[j - 1]:
                # We included interval j
                selected.append(interval)
                # Move to predecessor
                j = p[j - 1] + 1
            else:
                # We excluded interval j
                j -= 1

        return list(reversed(selected))

    def get_schedule_summary(
        self, selected_intervals: List[Interval]
    ) -> Dict[str, Any]:
        """Generate a human-readable summary of the chosen intervals.

        Args:
            selected_intervals: The list of selected intervals.

        Returns:
            dict: A dictionary containing stats and the timeline.
        """
        total_weight = sum(interval.weight for interval in selected_intervals)
        total_intervals = len(selected_intervals)
        timeline = [
            (
                f"Interval {i+1}",
                f"({interval.start}-{interval.end})",
                f"weight: {interval.weight}",
            )
            for i, interval in enumerate(selected_intervals)
        ]

        return {
            "total_weight": total_weight,
            "total_intervals": total_intervals,
            "schedule": timeline,
        }
