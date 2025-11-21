from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True, order=True)
class Interval:
    """Data model representing an interval.

    Attributes:
        start: Start time of the interval.
        end: End time of the interval.
        weight: Weight/value associated with the interval.
    """

    sort_index: Tuple[int, int, int] = field(init=False, repr=False)
    start: int = field(compare=False)
    end: int = field(compare=False)
    weight: int = field(compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sort_index", (self.end, self.start, self.weight))

    def as_tuple(self) -> Tuple[int, int, int]:
        """Return the interval as a (start, end, weight) tuple."""

        return (self.start, self.end, self.weight)


class AdvancedIntervalScheduler:
    """Weighted interval scheduling using dynamic programming."""

    def __init__(self, intervals: Iterable[Tuple[int, int, int] | Interval]):
        """Initialize the scheduler with interval data.

        Args:
            intervals: Iterable of (start, end, weight) tuples or :class:`Interval` objects.
        """

        self.intervals: List[Interval] = [
            interval
            if isinstance(interval, Interval)
            else Interval(start=interval[0], end=interval[1], weight=interval[2])
            for interval in intervals
        ]
        self.n = len(self.intervals)

    def find_optimal_schedule(self) -> Tuple[int, List[Interval]]:
        """Compute the maximum weight subset of non-overlapping intervals."""

        if not self.intervals:
            return 0, []

        sorted_intervals = sorted(self.intervals)
        end_times = [interval.end for interval in sorted_intervals]
        p = self._compute_predecessors(sorted_intervals, end_times)

        dp = [0] * (self.n + 1)

        for j in range(1, self.n + 1):
            interval = sorted_intervals[j - 1]
            include_weight = interval.weight + dp[p[j - 1] + 1]
            exclude_weight = dp[j - 1]
            dp[j] = max(include_weight, exclude_weight)

        selected = self._backtrack_schedule(dp, p, sorted_intervals)
        return dp[self.n], selected

    def _compute_predecessors(
        self, intervals: Sequence[Interval], end_times: Sequence[int]
    ) -> List[int]:
        """Compute p(i) for each interval.

        p(i) is the index of the rightmost interval that finishes no later than the
        start of interval *i*. If none exists, ``-1`` is used.
        """

        p = [-1] * self.n
        for j, interval in enumerate(intervals):
            i = bisect.bisect_right(end_times, interval.start, hi=j) - 1
            p[j] = i if i >= 0 and end_times[i] <= interval.start else -1
        return p

    def _backtrack_schedule(
        self, dp: Sequence[int], p: Sequence[int], intervals: Sequence[Interval]
    ) -> List[Interval]:
        """Reconstruct the chosen intervals from the DP table."""

        selected: List[Interval] = []
        j = self.n
        while j > 0:
            interval = intervals[j - 1]
            include_weight = interval.weight + dp[p[j - 1] + 1]
            if include_weight >= dp[j - 1]:
                selected.append(interval)
                j = p[j - 1] + 1
            else:
                j -= 1

        return list(reversed(selected))

    def get_schedule_summary(self, selected_intervals: List[Interval]) -> dict:
        """Generate a human-readable summary of the chosen intervals."""

        total_weight = sum(interval.weight for interval in selected_intervals)
        total_intervals = len(selected_intervals)
        timeline = [
            (f"Interval {i+1}", f"({interval.start}-{interval.end})", f"weight: {interval.weight}")
            for i, interval in enumerate(selected_intervals)
        ]

        return {
            "total_weight": total_weight,
            "total_intervals": total_intervals,
            "schedule": timeline,
        }
