"""Optimal algorithms for weighted interval scheduling.

The textbook solution sorts by finish time, binary-searches for each interval's
latest compatible predecessor `p(j)`, and fills a DP table: `O(n log n)` time,
with the `log` appearing **twice** (once in the sort, once in `n` binary
searches).

This module implements the algorithms that are actually optimal:

* :func:`schedule` -- a single left-to-right **event sweep**. It removes the
  binary searches entirely, so the running time is `O(sort(n)) + O(n)`. Nothing
  but the sort is superlinear.
* :func:`schedule_integer_endpoints` -- the same sweep over a **radix sort**,
  giving genuinely `O(n)` total time when endpoints are bounded integers, which
  beats the `Omega(n log n)` comparison-model lower bound by leaving that model.
* :func:`max_intervals` -- the unweighted special case, where a greedy rule is
  optimal and no DP is needed.
* :func:`schedule_k_machines` -- the generalisation to `k` parallel machines,
  solved exactly by min-cost flow. Greedy and the one-machine DP both fail here.

See ``OPTIMAL.md`` for the derivation, the lower-bound discussion, and the list
of approaches that do not work.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Interval",
    "Schedule",
    "schedule",
    "schedule_integer_endpoints",
    "schedule_binary_search",
    "max_intervals",
    "schedule_k_machines",
]


@dataclass(frozen=True)
class Interval:
    """A half-open interval ``[start, end)`` carrying a weight.

    Half-open is the right convention: two intervals are compatible exactly when
    one's end is ``<=`` the other's start, so an interval ending at 5 and one
    starting at 5 do not conflict.

    An interval with ``start == end`` is **empty**: it covers no point, so it
    conflicts with nothing and is always selectable. Every function in this
    module handles empty intervals by setting them aside and adding back the
    ones with positive weight, which keeps them out of the sweep -- an empty
    interval's END event would otherwise precede its own START event and let it
    become its own predecessor.
    """

    start: int
    end: int
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"interval end {self.end} precedes start {self.start}")

    @property
    def is_empty(self) -> bool:
        """``True`` if the interval covers no point."""
        return self.start == self.end

    def overlaps(self, other: "Interval") -> bool:
        """Return ``True`` if the two intervals share at least one point."""
        if self.is_empty or other.is_empty:
            return False
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Schedule:
    """The result of a scheduling call."""

    total_weight: float
    selected: List[Interval]

    def is_feasible(self, machines: int = 1) -> bool:
        """Check that no point in time is covered by more than ``machines`` intervals.

        Used by the tests as an independent verifier: the DP could be wrong, but
        this check does not depend on it.
        """
        events: List[Tuple[int, int]] = []
        for iv in self.selected:
            if iv.start != iv.end:
                events.append((iv.start, 1))
                events.append((iv.end, -1))
        events.sort()
        running = 0
        for _, delta in events:
            running += delta
            if running > machines:
                return False
        return True


def _coerce(intervals: Iterable) -> List[Interval]:
    """Accept ``Interval`` objects or ``(start, end, weight)`` tuples."""
    out: List[Interval] = []
    for item in intervals:
        if isinstance(item, Interval):
            out.append(item)
        else:
            start, end, *rest = item
            out.append(Interval(start, end, float(rest[0]) if rest else 1.0))
    return out


def _split_empty(items: List[Interval]) -> Tuple[List[Interval], List[Interval]]:
    """Separate the schedulable intervals from the always-selectable empty ones.

    Empty intervals conflict with nothing, so the optimal solution takes every
    one with positive weight and no others. Keeping them out of the sweep is
    also a correctness requirement: an empty interval's END event sorts before
    its own START event, which would let it be recorded as its own predecessor
    and turn the backtracking walk into an infinite loop.
    """
    real = [iv for iv in items if not iv.is_empty]
    free = [iv for iv in items if iv.is_empty and iv.weight > 0]
    return real, free


def _merge_empty(result: Schedule, free: List[Interval]) -> Schedule:
    """Fold the always-selectable empty intervals back into a schedule."""
    if not free:
        return result
    selected = sorted(result.selected + free, key=lambda iv: (iv.start, iv.end))
    return Schedule(result.total_weight + sum(iv.weight for iv in free), selected)


# --------------------------------------------------------------------------
# The optimal one-machine algorithm: a single event sweep
# --------------------------------------------------------------------------


def _sweep(items: List[Interval], order: Sequence[int], index_bits: int) -> Schedule:
    """Run the DP over a pre-sorted list of packed events.

    Each event is one integer, ``(coordinate << (index_bits + 1)) |
    (kind << index_bits) | interval_index``, with ``kind == 0`` for an END event
    and ``1`` for a START event. Packing the whole event into a single int means
    the sort compares machine integers instead of tuples, and needs no ``key``
    function -- worth roughly 2x in CPython. It also gets the tie-break right for
    free: at equal coordinates END sorts before START, which is exactly the
    half-open compatibility rule (``[a,b)`` and ``[b,c)`` do not conflict).

    **The invariant is the whole trick.** Sweeping left to right, ``best``
    always holds ``OPT`` over the intervals that have already *finished*. So:

    * at the START of interval ``j``, ``best`` is by definition ``OPT(p(j))`` --
      the best achievable using only intervals compatible with ``j``. Record it.
      No binary search is needed, because the sweep has already walked past
      exactly the right prefix.
    * at the END of ``j``, its own best value is ``recorded_j + w_j``; fold that
      into ``best``.

    That replaces `n` binary searches with `2n` sequential steps.
    """
    n = len(items)
    # value_if_taken[j] = OPT(p(j)), captured when j's start is swept.
    value_if_taken = [0.0] * n
    # predecessor[j] = last interval in the optimal chain ending before j starts.
    predecessor: List[Optional[int]] = [None] * n
    weights = [iv.weight for iv in items]

    index_mask = (1 << index_bits) - 1
    kind_bit = 1 << index_bits
    best = 0.0
    best_index: Optional[int] = None

    for event in order:
        j = event & index_mask
        if event & kind_bit:  # START of j
            value_if_taken[j] = best
            predecessor[j] = best_index
        else:  # END of j
            total = value_if_taken[j] + weights[j]
            if total > best:
                best = total
                best_index = j

    selected: List[Interval] = []
    cursor = best_index
    while cursor is not None:
        selected.append(items[cursor])
        cursor = predecessor[cursor]
    selected.reverse()
    return Schedule(total_weight=best, selected=selected)


def _pack_events(items: List[Interval]) -> Tuple[List[int], int]:
    """Build the packed event list and return it with the index width used."""
    n = len(items)
    index_bits = max(1, (n - 1).bit_length())
    shift = index_bits + 1
    kind_bit = 1 << index_bits
    # Shift coordinates non-negative so the packed key stays monotone in time.
    offset = min(min(iv.start for iv in items), 0)
    events = [((iv.end - offset) << shift) | j for j, iv in enumerate(items)]
    events += [
        ((iv.start - offset) << shift) | kind_bit | j for j, iv in enumerate(items)
    ]
    return events, index_bits


def schedule(intervals: Iterable) -> Schedule:
    """Maximum-weight set of pairwise non-overlapping intervals.

    Uses the event sweep: one sort, then a single `O(n)` pass. The textbook
    formulation spends a second `O(n log n)` on `n` binary searches for `p(j)`;
    this does not.

    Args:
        intervals: ``Interval`` objects or ``(start, end, weight)`` tuples.
            Endpoints must be integers (the event packing needs exact shifts);
            use :func:`schedule_binary_search` for float endpoints.

    Returns:
        A :class:`Schedule` with the optimal total weight and the chosen
        intervals in chronological order.

    Example:
        >>> result = schedule([(1, 3, 5), (2, 5, 6), (4, 6, 5), (6, 7, 8)])
        >>> result.total_weight
        18.0
        >>> [(i.start, i.end) for i in result.selected]
        [(1, 3), (4, 6), (6, 7)]
    """
    items = _coerce(intervals)
    for iv in items:
        if not isinstance(iv.start, int) or not isinstance(iv.end, int):
            raise TypeError(
                "schedule() requires integer endpoints; use schedule_binary_search"
            )
    items, free = _split_empty(items)
    if not items:
        return _merge_empty(Schedule(0.0, []), free)
    events, index_bits = _pack_events(items)
    events.sort()
    return _merge_empty(_sweep(items, events, index_bits), free)


def schedule_arrays(starts, ends, weights):
    """NumPy fast path: the same sweep, with the sort done in C.

    The sweep's sequential dependency (each `OPT(p(j))` is read off a running
    maximum that later steps update) cannot be vectorised. The *sort* can be,
    and the sort is the asymptotically dominant term -- so this is where the
    remaining speed is. Sorting a packed ``int64`` array with NumPy is about 5x
    faster than CPython's ``list.sort`` on the same values.

    The win only materialises if the caller already holds arrays; converting a
    list of tuples into arrays costs more than it saves. Use this when interval
    data arrives from a columnar source (Parquet, a dataframe, a binary file).

    Args:
        starts: Integer array of start times.
        ends: Integer array of end times.
        weights: Numeric array of weights.

    Returns:
        A tuple ``(total_weight, selected_indices)`` where ``selected_indices``
        is a sorted NumPy array of indices into the input arrays.

    Raises:
        ImportError: If NumPy is not installed.
    """
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError("schedule_arrays requires NumPy") from exc

    starts = np.asarray(starts, dtype=np.int64)
    ends = np.asarray(ends, dtype=np.int64)
    weights = np.asarray(weights, dtype=np.float64)
    n = int(starts.shape[0])
    if n == 0:
        return 0.0, np.empty(0, dtype=np.int64)

    index_bits = max(1, (n - 1).bit_length())
    shift = index_bits + 1
    offset = min(int(starts.min()), 0)
    idx = np.arange(n, dtype=np.int64)
    events = np.concatenate(
        [
            ((ends - offset) << shift) | idx,
            ((starts - offset) << shift) | (1 << index_bits) | idx,
        ]
    )
    events.sort()

    index_mask = (1 << index_bits) - 1
    kind_bit = 1 << index_bits
    value_if_taken = [0.0] * n
    predecessor: List[Optional[int]] = [None] * n
    weight_list = weights.tolist()
    best = 0.0
    best_index: Optional[int] = None

    for event in events.tolist():
        j = event & index_mask
        if event & kind_bit:
            value_if_taken[j] = best
            predecessor[j] = best_index
        else:
            total = value_if_taken[j] + weight_list[j]
            if total > best:
                best = total
                best_index = j

    chosen: List[int] = []
    cursor = best_index
    while cursor is not None:
        chosen.append(cursor)
        cursor = predecessor[cursor]
    chosen.reverse()
    return best, np.asarray(chosen, dtype=np.int64)


def _radix_sort(keys: List[int], max_key: int, radix_bits: int = 11) -> List[int]:
    """LSD radix sort of non-negative integers, base ``2**radix_bits``."""
    buckets_count = 1 << radix_bits
    mask = buckets_count - 1
    shift = 0
    while (max_key >> shift) > 0:
        buckets: List[List[int]] = [[] for _ in range(buckets_count)]
        for key in keys:
            buckets[(key >> shift) & mask].append(key)
        keys = [key for bucket in buckets for key in bucket]
        shift += radix_bits
    return keys


def schedule_integer_endpoints(intervals: Iterable) -> Schedule:
    """Weighted interval scheduling in `O(n)` time for bounded integer endpoints.

    Identical DP to :func:`schedule`, but the events are **radix**-sorted rather
    than comparison-sorted. When endpoints are integers over a polynomially
    bounded range -- timestamps, slot indices, seconds since epoch -- this is
    genuinely linear time, and therefore escapes the `Omega(n log n)`
    comparison-model lower bound that is usually quoted as the last word on this
    problem.

    **Honest caveat on CPython.** This is the asymptotically optimal variant, and
    in a compiled language it is also the fastest. In CPython it is *slower* than
    :func:`schedule`, because ``list.sort`` is C Timsort while this radix sort is
    interpreted bytecode: a ~3x constant-factor handicap that no amount of `n`
    within reach of a Python process will overcome. It is provided because it is
    the right algorithm, and measured rather than assumed. See ``OPTIMAL.md``.

    Args:
        intervals: ``Interval`` objects or ``(start, end, weight)`` tuples with
            integer endpoints.

    Returns:
        A :class:`Schedule`, identical to what :func:`schedule` returns.

    Raises:
        TypeError: If any endpoint is not an integer.
    """
    items = _coerce(intervals)
    for iv in items:
        if not isinstance(iv.start, int) or not isinstance(iv.end, int):
            raise TypeError("schedule_integer_endpoints requires integer endpoints")
    items, free = _split_empty(items)
    if not items:
        return _merge_empty(Schedule(0.0, []), free)

    events, index_bits = _pack_events(items)
    sweep = _sweep(items, _radix_sort(events, max(events)), index_bits)
    return _merge_empty(sweep, free)


def schedule_binary_search(intervals: Iterable) -> Schedule:
    """The textbook `p(j)` + binary search DP, kept for comparison and testing.

    Correct, and asymptotically the same `O(n log n)` as :func:`schedule`, but it
    performs `n` binary searches that the sweep shows to be unnecessary. Present
    so the tests can cross-check the sweep against an independent formulation.
    """
    import bisect

    items, free = _split_empty(_coerce(intervals))
    items.sort(key=lambda iv: iv.end)
    n = len(items)
    if n == 0:
        return _merge_empty(Schedule(0.0, []), free)

    ends = [iv.end for iv in items]
    # p[j]: count of intervals finishing at or before items[j].start.
    p = [bisect.bisect_right(ends, items[j].start) for j in range(n)]

    dp = [0.0] * (n + 1)
    for j in range(1, n + 1):
        take = items[j - 1].weight + dp[p[j - 1]]
        dp[j] = max(dp[j - 1], take)

    selected: List[Interval] = []
    j = n
    while j > 0:
        if items[j - 1].weight + dp[p[j - 1]] > dp[j - 1]:
            selected.append(items[j - 1])
            j = p[j - 1]
        else:
            j -= 1
    selected.reverse()
    return _merge_empty(Schedule(dp[n], selected), free)


# --------------------------------------------------------------------------
# The unweighted special case: greedy is optimal, DP is overkill
# --------------------------------------------------------------------------


def max_intervals(intervals: Iterable) -> Schedule:
    """Maximum *number* of pairwise non-overlapping intervals.

    When all weights are equal, the DP is unnecessary: repeatedly taking the
    interval with the earliest finish time is optimal. The exchange argument is
    the reason -- any optimal solution can be transformed, one interval at a
    time, into the greedy one without ever reducing its size, because swapping
    in the earliest-finishing compatible interval never blocks anything the
    replaced one allowed.

    Note this greedy is optimal *only* for equal weights. With weights it can be
    arbitrarily bad: one interval of weight 100 spanning the whole line versus
    two of weight 1 gives greedy a ratio of 2/100.

    Returns:
        A :class:`Schedule` whose ``total_weight`` is the count of selected
        intervals.
    """
    items, free = _split_empty(_coerce(intervals))
    items.sort(key=lambda iv: (iv.end, iv.start))
    selected: List[Interval] = []
    last_end: Optional[int] = None
    for iv in items:
        if last_end is None or iv.start >= last_end:
            selected.append(iv)
            last_end = iv.end
    combined = sorted(selected + free, key=lambda iv: (iv.start, iv.end))
    return Schedule(float(len(combined)), combined)


# --------------------------------------------------------------------------
# k parallel machines: min-cost flow
# --------------------------------------------------------------------------


class _MinCostFlow:
    """Successive-shortest-paths min-cost flow with Johnson potentials.

    Edge costs here are negative (they are negated weights), so the first
    potential pass uses the fact that the initial graph is a DAG in coordinate
    order and computes exact distances by relaxing vertices in that order.
    Subsequent passes use Dijkstra on the reduced costs, which are non-negative
    by the standard potential argument.
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.graph: List[List[List[int]]] = [[] for _ in range(size)]

    def add_edge(self, u: int, v: int, capacity: int, cost: int) -> None:
        """Add a directed edge with the paired residual arc."""
        self.graph[u].append([v, capacity, cost, len(self.graph[v])])
        self.graph[v].append([u, 0, -cost, len(self.graph[u]) - 1])

    def flow(self, source: int, sink: int, amount: int) -> Tuple[int, int]:
        """Push up to ``amount`` units and return ``(units_pushed, total_cost)``.

        Stops early once no further augmenting path has negative cost, which is
        what makes this solve the *maximum weight* problem rather than being
        forced to route all ``amount`` units.
        """
        n = self.size
        INF = float("inf")

        # Initial potentials: the graph is a DAG on 0..n-1 by construction, so
        # relaxing vertices in index order gives exact shortest distances even
        # with negative edges.
        potential = [0] * n
        dist = [INF] * n
        dist[source] = 0
        for u in range(n):
            if dist[u] == INF:
                continue
            for v, cap, cost, _ in self.graph[u]:
                if cap > 0 and dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
        for v in range(n):
            potential[v] = 0 if dist[v] == INF else dist[v]

        total_flow = 0
        total_cost = 0
        while total_flow < amount:
            dist = [INF] * n
            dist[source] = 0
            prev_v = [-1] * n
            prev_e = [-1] * n
            heap: List[Tuple[float, int]] = [(0, source)]
            while heap:
                d, u = heapq.heappop(heap)
                if d > dist[u]:
                    continue
                for i, (v, cap, cost, _) in enumerate(self.graph[u]):
                    if cap <= 0:
                        continue
                    nd = d + cost + potential[u] - potential[v]
                    if nd < dist[v]:
                        dist[v] = nd
                        prev_v[v] = u
                        prev_e[v] = i
                        heapq.heappush(heap, (nd, v))
            if dist[sink] == INF:
                break

            for v in range(n):
                if dist[v] < INF:
                    potential[v] += dist[v]
            # True cost of this path in the original (un-reduced) costs.
            path_cost = potential[sink] - potential[source]
            if path_cost >= 0:
                # Any further augmentation would only reduce total weight.
                break

            # Bottleneck along the path.
            push = amount - total_flow
            v = sink
            while v != source:
                push = min(push, self.graph[prev_v[v]][prev_e[v]][1])
                v = prev_v[v]
            v = sink
            while v != source:
                edge = self.graph[prev_v[v]][prev_e[v]]
                edge[1] -= push
                self.graph[v][edge[3]][1] += push
                v = prev_v[v]

            total_flow += push
            total_cost += push * path_cost
        return total_flow, total_cost


def schedule_k_machines(intervals: Iterable, machines: int) -> Schedule:
    """Maximum-weight interval selection when ``k`` intervals may overlap.

    This is the real generalisation of the challenge, and it is where the
    one-machine DP and every greedy rule break down: the problem stops being a
    chain and becomes a flow.

    **The reduction.** Compress all endpoints to positions on a line and build a
    path graph over them, each consecutive pair joined by an edge of capacity
    ``k`` and cost 0. Add, for each interval, an edge from its start position to
    its end position with capacity 1 and cost ``-weight``. Push ``k`` units from
    the leftmost to the rightmost coordinate at minimum cost. A unit of flow is
    one machine's timeline; an interval edge carrying flow is a scheduled
    interval; capacity ``k`` on the path edges is exactly the constraint that no
    instant is oversubscribed.

    Because costs are negative, minimum cost maximises total weight, and the
    solver stops augmenting once paths stop being profitable -- so it selects the
    best subset rather than being forced to fill every machine.

    Args:
        intervals: ``Interval`` objects or ``(start, end, weight)`` tuples.
        machines: Number of intervals allowed to overlap at any instant.

    Returns:
        A :class:`Schedule`. For ``machines == 1`` it agrees with
        :func:`schedule`.

    Raises:
        ValueError: If ``machines`` is not positive.

    Complexity:
        `O(k * E log V)` with `V = O(n)` distinct coordinates and `E = O(n)`.

    Note:
        Weights are scaled to integers internally, so float weights are rounded
        to six decimal places.
    """
    if machines < 1:
        raise ValueError("machines must be at least 1")
    items, free = _split_empty(_coerce(intervals))
    if not items:
        return _merge_empty(Schedule(0.0, []), free)
    if machines == 1:
        return _merge_empty(schedule(items), free)

    coords = sorted({c for iv in items for c in (iv.start, iv.end)})
    index: Dict[int, int] = {c: i for i, c in enumerate(coords)}

    scale = 1_000_000
    net = _MinCostFlow(len(coords))
    for i in range(len(coords) - 1):
        net.add_edge(i, i + 1, machines, 0)
    edge_of: List[Tuple[int, int]] = []
    for iv in items:
        u = index[iv.start]
        edge_of.append((u, len(net.graph[u])))
        net.add_edge(u, index[iv.end], 1, -round(iv.weight * scale))

    net.flow(0, len(coords) - 1, machines)

    selected = [
        iv
        for iv, (u, e) in zip(items, edge_of)
        if net.graph[u][e][1] == 0  # capacity consumed => interval chosen
    ]
    selected.sort(key=lambda iv: (iv.start, iv.end))
    return _merge_empty(Schedule(sum(iv.weight for iv in selected), selected), free)


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import random
    import time

    demo = [(1, 3, 5), (2, 5, 6), (4, 6, 5), (6, 7, 8), (5, 8, 11)]
    result = schedule(demo)
    print(f"sweep            weight={result.total_weight}")
    print(
        f"                 chosen={[(i.start, i.end, i.weight) for i in result.selected]}"
    )
    print(f"binary-search DP weight={schedule_binary_search(demo).total_weight}")
    print(f"2 machines       weight={schedule_k_machines(demo, 2).total_weight}")
    print(f"unweighted count weight={max_intervals(demo).total_weight}")

    rng = random.Random(7)
    big = []
    for _ in range(200_000):
        s = rng.randrange(0, 2_000_000)
        big.append((s, s + rng.randrange(1, 500), rng.randrange(1, 1000)))

    print(f"\n{len(big)} intervals:")
    for name, fn in (
        ("sweep (packed int sort)", schedule),
        ("sweep (radix sort)", schedule_integer_endpoints),
        ("textbook binary search", schedule_binary_search),
    ):
        t0 = time.perf_counter()
        out = fn(big)
        print(
            f"  {name:<26} {time.perf_counter() - t0:6.2f}s  weight={out.total_weight:.0f}"
        )

    try:
        import numpy as np

        starts = np.array([b[0] for b in big], dtype=np.int64)
        ends = np.array([b[1] for b in big], dtype=np.int64)
        weights = np.array([b[2] for b in big], dtype=np.float64)
        t0 = time.perf_counter()
        total, _ = schedule_arrays(starts, ends, weights)
        print(
            f"  {'sweep (numpy sort)':<26} {time.perf_counter() - t0:6.2f}s  weight={total:.0f}"
        )
    except ImportError:
        pass
