"""Heavy hitters in a stream: the optimal structures, and what each is optimal for.

"Find the top k" in a stream has no single best answer, because there are three
different guarantees on offer and they are not comparable:

* **Deterministic, mergeable, provably space-optimal.** :class:`MisraGries` with
  ``1/eps`` counters gives every item an estimate within ``eps*N`` of the truth,
  never over-counts, and -- the property that matters for distributed systems --
  two summaries can be **merged** into a summary of the concatenated streams.
  ``Theta(1/eps)`` counters is a matching lower bound, so nothing does better
  under this guarantee.

* **Same bound, better estimates, O(1) worst case.** :class:`StreamSummary` is
  Space-Saving backed by the bucket structure from the original paper. The
  version usually written scans all ``k`` counters to find the minimum on every
  eviction; grouping counters into count-buckets makes the minimum ``O(1)`` to
  find, so updates are ``O(1)`` **worst case**, not amortised.

* **Unbiased estimates.** Space-Saving systematically *over*-counts, because an
  evicted item's count is inherited by its replacement.
  :class:`UnbiasedSpaceSaving` (Ting, KDD 2018) replaces deterministic eviction
  with a randomised one, making the estimator unbiased -- which is what you need
  when the counts are summed or averaged downstream rather than just ranked.

* **Resistance to a heavy tail.** :class:`HeavyKeeper` (USENIX ATC 2018)
  abandons the additive-error guarantee entirely and uses
  count-with-exponential-decay, evicting small flows aggressively while barely
  touching large ones. Measured here, its advantage is **conditional on the
  workload**: it beats Space-Saving on lightly skewed streams, where tail noise
  keeps knocking real heavy hitters out of a Space-Saving table, and loses on
  heavily skewed ones, where Space-Saving retains the top items easily and its
  exact counting wins. See ``OPTIMAL.md`` for the measurements.

:func:`compare` measures all four on a Zipfian stream. See ``OPTIMAL.md``.
"""

from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Estimate",
    "MisraGries",
    "StreamSummary",
    "UnbiasedSpaceSaving",
    "HeavyKeeper",
    "Accuracy",
    "evaluate",
    "compare",
    "zipf_stream",
]

Item = Hashable


@dataclass(frozen=True)
class Estimate:
    """An item's estimated frequency and the uncertainty around it."""

    item: Item
    count: int
    error: int = 0

    @property
    def lower_bound(self) -> int:
        """Guaranteed lower bound on the true frequency."""
        return self.count - self.error

    def __repr__(self) -> str:
        return f"Estimate({self.item!r}, {self.count}, +/-{self.error})"


# --------------------------------------------------------------------------
# Misra-Gries: deterministic, space-optimal, mergeable
# --------------------------------------------------------------------------


class MisraGries:
    """Misra-Gries summary (1982): the space-optimal deterministic answer.

    Keep ``k-1`` counters. On each arrival, increment a matching counter, or
    claim a free one, or -- if neither -- **decrement every counter by one** and
    drop those that hit zero.

    **Why it works.** Each decrement round discards `k` distinct items at once.
    An item occurring more than `N/k` times cannot be fully cancelled, because
    there are fewer than `N/k` such rounds. So every item with frequency above
    `N/k` survives, and every estimate undercounts by at most `N/k`.

    **The property the others lack: mergeability.** Two summaries can be
    combined into a summary of the concatenated streams with the same error
    bound -- add the counters, then subtract the ``(k)``-th largest value and
    drop the non-positive entries. That makes it the right structure for
    distributed aggregation, where each shard summarises locally and the
    summaries are combined. Space-Saving and HeavyKeeper have no such operation.

    Example:
        >>> mg = MisraGries(k=3)
        >>> mg.update_many("aabacada")
        >>> [e.item for e in mg.heavy_hitters()]
        ['a']
    """

    def __init__(self, k: int) -> None:
        """Create a summary that finds every item occurring more than ``N/k`` times.

        Args:
            k: Frequency threshold parameter. Uses ``k-1`` counters.

        Raises:
            ValueError: If ``k`` is less than 2.
        """
        if k < 2:
            raise ValueError("k must be at least 2")
        self.k = k
        self.capacity = k - 1
        self.counters: Dict[Item, int] = {}
        self.total = 0

    def update(self, item: Item, weight: int = 1) -> None:
        """Observe ``item``.

        Args:
            item: The stream element.
            weight: How many occurrences to record. Applied as repeated unit
                updates, which keeps this the textbook algorithm exactly.

        Raises:
            ValueError: If ``weight`` is not positive.
        """
        if weight <= 0:
            raise ValueError("weight must be positive")
        for _ in range(weight):
            self._update_one(item)

    def _update_one(self, item: Item) -> None:
        self.total += 1
        if item in self.counters:
            self.counters[item] += 1
        elif len(self.counters) < self.capacity:
            self.counters[item] = 1
        else:
            # No free counter: cancel this occurrence against one occurrence of
            # every counter currently held. That discards k distinct items at
            # once, which is why an item above N/k cannot be fully cancelled.
            for key in list(self.counters):
                self.counters[key] -= 1
                if self.counters[key] == 0:
                    del self.counters[key]

    def update_many(self, items: Iterable[Item]) -> None:
        """Observe every element of ``items``."""
        for item in items:
            self._update_one(item)

    def estimate(self, item: Item) -> Estimate:
        """Return the estimated frequency of ``item``.

        The estimate never exceeds the true frequency, and undershoots it by at
        most ``total / k``.
        """
        count = self.counters.get(item, 0)
        return Estimate(item, count, error=self.total // self.k)

    def heavy_hitters(self, threshold: Optional[float] = None) -> List[Estimate]:
        """Return items that may occur more than ``threshold * total`` times.

        Args:
            threshold: Fraction of the stream. Defaults to ``1/k``.

        Returns:
            Estimates sorted by decreasing count. Contains every true heavy
            hitter, and possibly some false ones -- verify with a second pass if
            exactness is required.
        """
        if threshold is None:
            threshold = 1.0 / self.k
        cutoff = threshold * self.total - self.total / self.k
        return sorted(
            (
                Estimate(item, count, error=self.total // self.k)
                for item, count in self.counters.items()
                if count >= cutoff
            ),
            key=lambda e: -e.count,
        )

    def top_k(self, k: int) -> List[Estimate]:
        """Return the ``k`` highest-count entries."""
        return sorted(
            (Estimate(i, c, self.total // self.k) for i, c in self.counters.items()),
            key=lambda e: -e.count,
        )[:k]

    def merge(self, other: "MisraGries") -> "MisraGries":
        """Merge another summary into this one, in place.

        Implements the mergeable Misra-Gries of Agarwal et al. (2012): add the
        counters, then subtract the ``(capacity+1)``-th largest value from all
        of them and drop non-positive entries. The error bound of the result is
        the same as if the concatenated stream had been summarised directly.

        Args:
            other: A summary with the same ``k``.

        Returns:
            ``self``, for chaining.

        Raises:
            ValueError: If the summaries were built with different ``k``.
        """
        if other.k != self.k:
            raise ValueError(f"cannot merge k={other.k} into k={self.k}")
        for item, count in other.counters.items():
            self.counters[item] = self.counters.get(item, 0) + count
        self.total += other.total

        if len(self.counters) > self.capacity:
            ordered = sorted(self.counters.values(), reverse=True)
            cutoff = ordered[self.capacity]
            for key in list(self.counters):
                self.counters[key] -= cutoff
                if self.counters[key] <= 0:
                    del self.counters[key]
        return self

    def __len__(self) -> int:
        return len(self.counters)


# --------------------------------------------------------------------------
# Space-Saving with the bucket structure: O(1) worst case
# --------------------------------------------------------------------------


class StreamSummary:
    """Space-Saving with the Stream-Summary structure (Metwally et al., ICDT 2005).

    Keep `k` counters. On a miss with the table full, **evict the item with the
    smallest count**, give its slot to the new item, and record the evicted
    count as that entry's error. Every estimate is then an over-count by at most
    that error, and the true count is guaranteed to lie in
    ``[count - error, count]``.

    **The optimisation this class exists for.** The obvious implementation scans
    all `k` counters to find the minimum on every eviction, making updates
    `O(k)`. Grouping counters by their count -- so that all items with count `c`
    live together, and the buckets are kept in ascending order -- makes the
    minimum `O(1)` to find and `O(1)` to maintain, because a count only ever
    moves by exactly one.

    That the minimum bucket advances by exactly one when it empties is the
    invariant that makes it work: items leave a bucket only by being incremented
    into the next one, so an emptied minimum bucket is always succeeded by the
    bucket immediately above it. Tracking the minimum therefore costs a single
    increment, not a search.

    The result is `O(1)` **worst case** per update rather than amortised, which
    is what makes it usable in a packet-processing path where tail latency, not
    average latency, is the constraint.

    Example:
        >>> ss = StreamSummary(k=3)
        >>> ss.update_many("aabacada")
        >>> [e.item for e in ss.top_k(1)]
        ['a']
    """

    def __init__(self, k: int) -> None:
        """Create a summary with ``k`` counters.

        Raises:
            ValueError: If ``k`` is not positive.
        """
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self.total = 0
        self.counts: Dict[Item, int] = {}
        self.errors: Dict[Item, int] = {}
        # count -> the set of items currently at that count.
        self.buckets: Dict[int, Set[Item]] = {}
        self.min_count = 0

    def _place(self, item: Item, count: int) -> None:
        """Put ``item`` into the bucket for ``count``."""
        self.buckets.setdefault(count, set()).add(item)

    def _lift(self, item: Item, old: int) -> None:
        """Move ``item`` from bucket ``old`` to bucket ``old + 1``."""
        bucket = self.buckets[old]
        bucket.discard(item)
        if not bucket:
            del self.buckets[old]
            if old == self.min_count:
                # The invariant: an emptied minimum bucket is always succeeded
                # by the one immediately above, because the only way out of a
                # bucket is an increment into the next.
                self.min_count = old + 1
        self._place(item, old + 1)

    def update(self, item: Item, weight: int = 1) -> None:
        """Observe ``item``.

        Args:
            item: The stream element.
            weight: How many occurrences to record. Weights above 1 are applied
                as repeated unit updates so the bucket invariant holds.

        Raises:
            ValueError: If ``weight`` is not positive.
        """
        if weight <= 0:
            raise ValueError("weight must be positive")
        for _ in range(weight):
            self._update_one(item)

    def _update_one(self, item: Item) -> None:
        self.total += 1
        if item in self.counts:
            old = self.counts[item]
            self.counts[item] = old + 1
            self._lift(item, old)
            return

        if len(self.counts) < self.k:
            self.counts[item] = 1
            self.errors[item] = 0
            self._place(item, 1)
            self.min_count = 1
            return

        # Full: evict from the minimum bucket, which is O(1) to reach.
        victim = next(iter(self.buckets[self.min_count]))
        evicted = self.counts.pop(victim)
        self.errors.pop(victim, None)
        self.buckets[self.min_count].discard(victim)
        if not self.buckets[self.min_count]:
            del self.buckets[self.min_count]

        # The new item inherits the evicted count -- which is exactly why
        # Space-Saving over-counts, and what the error field records.
        self.counts[item] = evicted + 1
        self.errors[item] = evicted
        self._place(item, evicted + 1)
        # The new item sits at min_count + 1, so if the minimum bucket just
        # emptied, the bucket above it is guaranteed non-empty. No search.
        if self.min_count not in self.buckets:
            self.min_count += 1

    def update_many(self, items: Iterable[Item]) -> None:
        """Observe every element of ``items``."""
        for item in items:
            self._update_one(item)

    def estimate(self, item: Item) -> Estimate:
        """Return the estimated frequency of ``item``.

        The estimate never *under*-counts, and over-counts by at most
        ``error``, so the true frequency lies in ``[count - error, count]``.
        """
        if item not in self.counts:
            return Estimate(item, 0, error=self.min_count)
        return Estimate(item, self.counts[item], self.errors.get(item, 0))

    def top_k(self, k: Optional[int] = None) -> List[Estimate]:
        """Return the ``k`` highest-count entries, most frequent first."""
        k = self.k if k is None else k
        return sorted(
            (Estimate(i, c, self.errors.get(i, 0)) for i, c in self.counts.items()),
            key=lambda e: -e.count,
        )[:k]

    def heavy_hitters(self, threshold: float = 0.0) -> List[Estimate]:
        """Return entries whose guaranteed lower bound exceeds ``threshold * total``.

        Using the lower bound rather than the raw count makes this list free of
        false positives: everything returned really does occur that often.
        """
        cutoff = threshold * self.total
        return [e for e in self.top_k(self.k) if e.lower_bound > cutoff]

    def __len__(self) -> int:
        return len(self.counts)


# --------------------------------------------------------------------------
# Unbiased Space-Saving
# --------------------------------------------------------------------------


class UnbiasedSpaceSaving:
    """Space-Saving with randomised eviction, giving unbiased estimates (Ting, KDD 2018).

    Plain Space-Saving always hands the evicted count to the incoming item,
    which means every retained estimate is biased *upward*. When the counts are
    only used to rank items, the bias is harmless. When they are summed,
    averaged, or fed into a downstream estimator, it accumulates.

    The fix is a one-line change with a real theoretical justification: on a
    miss with the table full, keep the incumbent with probability
    ``c / (c + 1)`` and replace it with probability ``1 / (c + 1)``, where ``c``
    is the minimum count. The counter is incremented either way. This makes the
    resulting counts an **unbiased estimator** of the true frequencies -- the
    procedure is equivalent to a priority sample of the stream.

    The trade is that estimates are no longer one-sided: an individual count may
    now be too low as well as too high. Bias and variance, as usual.
    """

    def __init__(self, k: int, seed: int = 0) -> None:
        """Create a summary with ``k`` counters.

        Args:
            k: Number of counters.
            seed: Seed for the eviction coin, so runs are reproducible.

        Raises:
            ValueError: If ``k`` is not positive.
        """
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self.total = 0
        self.counts: Dict[Item, int] = {}
        self.buckets: Dict[int, Set[Item]] = {}
        self.min_count = 0
        self._rng = random.Random(seed)

    def update(self, item: Item, weight: int = 1) -> None:
        """Observe ``item`` ``weight`` times.

        Raises:
            ValueError: If ``weight`` is not positive.
        """
        if weight <= 0:
            raise ValueError("weight must be positive")
        for _ in range(weight):
            self._update_one(item)

    def _update_one(self, item: Item) -> None:
        self.total += 1
        if item in self.counts:
            old = self.counts[item]
            self.counts[item] = old + 1
            bucket = self.buckets[old]
            bucket.discard(item)
            if not bucket:
                del self.buckets[old]
                if old == self.min_count:
                    self.min_count = old + 1
            self.buckets.setdefault(old + 1, set()).add(item)
            return

        if len(self.counts) < self.k:
            self.counts[item] = 1
            self.buckets.setdefault(1, set()).add(item)
            self.min_count = 1
            return

        smallest = self.min_count
        victim = next(iter(self.buckets[smallest]))
        # The whole difference from Space-Saving: a coin, not a certainty.
        replace = self._rng.random() < 1.0 / (smallest + 1)
        self.buckets[smallest].discard(victim)
        if not self.buckets[smallest]:
            del self.buckets[smallest]
        del self.counts[victim]

        keeper = item if replace else victim
        self.counts[keeper] = smallest + 1
        self.buckets.setdefault(smallest + 1, set()).add(keeper)
        # As in StreamSummary: the survivor lands one bucket above, so an
        # emptied minimum is always succeeded by the next bucket up.
        if self.min_count not in self.buckets:
            self.min_count += 1

    def update_many(self, items: Iterable[Item]) -> None:
        """Observe every element of ``items``."""
        for item in items:
            self._update_one(item)

    def estimate(self, item: Item) -> Estimate:
        """Return the unbiased estimated frequency of ``item``."""
        return Estimate(item, self.counts.get(item, 0), error=0)

    def top_k(self, k: Optional[int] = None) -> List[Estimate]:
        """Return the ``k`` highest-count entries, most frequent first."""
        k = self.k if k is None else k
        return sorted(
            (Estimate(i, c) for i, c in self.counts.items()), key=lambda e: -e.count
        )[:k]

    def __len__(self) -> int:
        return len(self.counts)


# --------------------------------------------------------------------------
# HeavyKeeper
# --------------------------------------------------------------------------


class HeavyKeeper:
    """HeavyKeeper (Gong et al., USENIX ATC 2018): count-with-exponential-decay.

    Space-Saving's weakness is that a brand-new item immediately inherits the
    smallest retained count, so a stream with a long tail of one-off items keeps
    knocking real heavy hitters out of the table and replacing them with noise.

    HeavyKeeper attacks exactly that. Each cell holds a *fingerprint* and a
    count. On a collision with a different fingerprint, the cell's count is
    decayed by one only with probability ``b^-count`` -- so a cell holding a
    large count is almost never disturbed, while a cell holding a small one is
    evicted quickly. Small flows decay away; large flows are protected by their
    own size.

    **When it actually wins.** The published claim is a large error reduction
    against the state of the art at equal memory. Measured on Zipfian streams
    over 5,000 items with a 64-cell budget, the advantage is conditional on how
    skewed the stream is:

    ==========  ==================  =====================  =========
    Zipf skew   HeavyKeeper recall  Space-Saving recall    HK wins
    ==========  ==================  =====================  =========
    1.0         **0.797**           0.734                  7 of 8
    1.1         0.781               **0.852**              3 of 8
    1.3         0.820               **0.992**              0 of 8
    ==========  ==================  =====================  =========

    The pattern makes sense from the mechanism: decay protects heavy hitters
    from a noisy tail, so it helps most where the tail is heaviest relative to
    the head. Where the head already dominates, Space-Saving keeps the top items
    without effort and its exact counting is simply more accurate.

    **What it gives up.** There is no additive-error guarantee and no lower
    bound on retained counts: this is a top-k structure, not a heavy-hitters
    structure with a proof attached. It is also not mergeable. Use
    :class:`MisraGries` when a guarantee is required, and this when the stream
    has a long noisy tail.
    """

    def __init__(
        self,
        k: int,
        width: Optional[int] = None,
        depth: int = 4,
        decay_base: float = 1.08,
        seed: int = 0,
    ) -> None:
        """Create a HeavyKeeper sketch.

        Args:
            k: How many top items to track.
            width: Cells per row. Defaults to ``8 * k``, which is the usual
                sizing for the reported accuracy.
            depth: Number of rows (independent hash functions).
            decay_base: The ``b`` in ``b^-count``. Larger protects big flows
                more strongly and evicts small ones more slowly.
            seed: Hash seed, so runs are reproducible.

        Raises:
            ValueError: If any parameter is out of range.
        """
        if k <= 0:
            raise ValueError("k must be positive")
        if depth <= 0:
            raise ValueError("depth must be positive")
        if decay_base <= 1.0:
            raise ValueError("decay_base must exceed 1")
        self.k = k
        self.width = width if width is not None else max(8 * k, 16)
        self.depth = depth
        self.decay_base = decay_base
        self.total = 0
        self._rng = random.Random(seed)
        self._fingerprints = [[0] * self.width for _ in range(depth)]
        self._counts = [[0] * self.width for _ in range(depth)]
        # A min-heap of (count, item) for the top-k set, plus a dict view.
        self._heap: List[Tuple[int, Item]] = []
        self._tracked: Dict[Item, int] = {}
        # Precompute the decay probabilities; b^-c underflows to 0 quickly, so
        # a short table covers every value that is not effectively zero.
        self._decay = [decay_base**-c for c in range(256)]

    def _cell(self, item: Item, row: int) -> Tuple[int, int]:
        """Return ``(index, fingerprint)`` for ``item`` in ``row``."""
        h = hash((item, row * 0x9E3779B1))
        return (h % self.width, (h >> 20) & 0xFFFF or 1)

    def update(self, item: Item, weight: int = 1) -> None:
        """Observe ``item`` ``weight`` times.

        Raises:
            ValueError: If ``weight`` is not positive.
        """
        if weight <= 0:
            raise ValueError("weight must be positive")
        for _ in range(weight):
            self._update_one(item)

    def _update_one(self, item: Item) -> None:
        self.total += 1
        best = 0
        for row in range(self.depth):
            index, fingerprint = self._cell(item, row)
            cell_fp = self._fingerprints[row][index]
            cell_count = self._counts[row][index]

            if cell_count == 0:
                self._fingerprints[row][index] = fingerprint
                self._counts[row][index] = 1
                best = max(best, 1)
            elif cell_fp == fingerprint:
                self._counts[row][index] = cell_count + 1
                best = max(best, cell_count + 1)
            else:
                # Exponential decay: a large count is almost never disturbed.
                probability = (
                    self._decay[cell_count] if cell_count < len(self._decay) else 0.0
                )
                if probability > 0.0 and self._rng.random() < probability:
                    self._counts[row][index] = cell_count - 1
                    if cell_count - 1 == 0:
                        self._fingerprints[row][index] = fingerprint
                        self._counts[row][index] = 1
                        best = max(best, 1)
        if best:
            self._offer(item, best)

    def _offer(self, item: Item, count: int) -> None:
        """Maintain the top-k set against a fresh estimate."""
        if item in self._tracked:
            if count > self._tracked[item]:
                self._tracked[item] = count
                heapq.heappush(self._heap, (count, item))
            return
        if len(self._tracked) < self.k:
            self._tracked[item] = count
            heapq.heappush(self._heap, (count, item))
            return
        # Drop stale heap entries, then compare against the true minimum.
        while self._heap:
            low_count, low_item = self._heap[0]
            if self._tracked.get(low_item) == low_count:
                break
            heapq.heappop(self._heap)
        if self._heap and count > self._heap[0][0]:
            _, evicted = heapq.heappop(self._heap)
            self._tracked.pop(evicted, None)
            self._tracked[item] = count
            heapq.heappush(self._heap, (count, item))

    def update_many(self, items: Iterable[Item]) -> None:
        """Observe every element of ``items``."""
        for item in items:
            self._update_one(item)

    def estimate(self, item: Item) -> Estimate:
        """Return the estimated frequency of ``item``.

        The estimate is the maximum count across rows whose fingerprint matches.
        """
        best = 0
        for row in range(self.depth):
            index, fingerprint = self._cell(item, row)
            if self._fingerprints[row][index] == fingerprint:
                best = max(best, self._counts[row][index])
        return Estimate(item, best, error=0)

    def top_k(self, k: Optional[int] = None) -> List[Estimate]:
        """Return the ``k`` most frequent items, most frequent first."""
        k = self.k if k is None else k
        return sorted(
            (self.estimate(item) for item in self._tracked), key=lambda e: -e.count
        )[:k]

    def __len__(self) -> int:
        return len(self._tracked)


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------


def zipf_stream(
    distinct: int, length: int, skew: float = 1.1, seed: int = 0
) -> List[int]:
    """Generate a Zipf-distributed stream, the standard heavy-hitters workload.

    Real streams -- web requests, network flows, search queries -- are heavily
    skewed, and every structure here is designed for that. Testing on a uniform
    stream measures nothing useful: there are no heavy hitters to find.

    Args:
        distinct: Number of distinct items.
        length: Stream length.
        skew: Zipf exponent. Higher means more skewed.
        seed: Random seed.

    Returns:
        A list of item ids, most frequent first in expectation.
    """
    weights = [1.0 / (rank**skew) for rank in range(1, distinct + 1)]
    total = sum(weights)
    cumulative = []
    running = 0.0
    for weight in weights:
        running += weight / total
        cumulative.append(running)

    import bisect

    rng = random.Random(seed)
    return [bisect.bisect(cumulative, rng.random()) for _ in range(length)]


@dataclass(frozen=True)
class Accuracy:
    """How well a structure recovered the true top-k."""

    name: str
    #: Fraction of the true top-k that the structure reported.
    recall: float
    #: Mean absolute relative error over the items it retained.
    average_relative_error: float
    #: Mean signed relative error over *all* true heavy hitters, counting a
    #: missed one as zero. Near 0 means the estimator is unbiased.
    bias: float
    #: Counters actually in use.
    counters: int

    def __str__(self) -> str:
        return (
            f"{self.name:<21} recall={self.recall:6.1%}  "
            f"err(kept)={self.average_relative_error:7.3%}  "
            f"bias(all)={self.bias:+8.3%}  counters={self.counters:>4}"
        )


def evaluate(name: str, summary: object, stream: Sequence[Item], k: int) -> Accuracy:
    """Measure a summary's top-k recall and estimation error against ground truth.

    Three numbers, because they answer three different questions and combining
    them hides the distinctions that decide which structure to use:

    * ``recall`` -- did it find the heavy hitters at all?
    * ``average_relative_error`` -- over the items it *retained*, how good are
      the counts? Scoring un-retained items here would just re-count the recall
      failure as an estimation failure.
    * ``bias`` -- over *all* true heavy hitters, counting a missed one as an
      estimate of zero. This is the measurement that tests unbiasedness, and it
      must include the misses: an estimator is unbiased unconditionally, and
      conditioning on "was retained" reintroduces a positive selection bias.
      Measuring bias only over survivors makes every structure look biased
      upward and hides the property entirely.

    Args:
        name: Label for the report.
        summary: Any object exposing ``top_k`` and ``estimate``.
        stream: The stream that was fed to it.
        k: How many top items to score.

    Returns:
        An :class:`Accuracy` report.
    """
    truth: Dict[Item, int] = {}
    for item in stream:
        truth[item] = truth.get(item, 0) + 1
    true_top = sorted(truth.items(), key=lambda kv: -kv[1])[:k]
    true_items = {item for item, _ in true_top}

    reported = summary.top_k(k)  # type: ignore[attr-defined]
    reported_items = {e.item for e in reported}
    recall = len(true_items & reported_items) / len(true_items) if true_items else 1.0

    retained_errors = []
    all_errors = []
    for item, actual in true_top:
        estimated = summary.estimate(item).count  # type: ignore[attr-defined]
        relative = (estimated - actual) / actual
        all_errors.append(relative if item in reported_items else -1.0)
        if item in reported_items:
            retained_errors.append(relative)

    return Accuracy(
        name=name,
        recall=recall,
        average_relative_error=(
            sum(abs(e) for e in retained_errors) / len(retained_errors)
            if retained_errors
            else 0.0
        ),
        bias=sum(all_errors) / len(all_errors) if all_errors else 0.0,
        counters=len(summary),  # type: ignore[arg-type]
    )


def compare(
    distinct: int = 20_000,
    length: int = 500_000,
    skew: float = 1.1,
    k: int = 50,
    counters: int = 200,
) -> List[Accuracy]:
    """Run every structure over the same Zipfian stream and score them.

    Args:
        distinct: Number of distinct items in the stream.
        length: Stream length.
        skew: Zipf exponent.
        k: How many top items to recover.
        counters: Memory budget, in counters, given to each structure.

    Returns:
        One :class:`Accuracy` per structure.
    """
    stream = zipf_stream(distinct, length, skew)
    results = []

    mg = MisraGries(k=counters)
    mg.update_many(stream)
    results.append(evaluate("MisraGries", mg, stream, k))

    ss = StreamSummary(k=counters)
    ss.update_many(stream)
    results.append(evaluate("StreamSummary", ss, stream, k))

    uss = UnbiasedSpaceSaving(k=counters, seed=1)
    uss.update_many(stream)
    results.append(evaluate("UnbiasedSpaceSaving", uss, stream, k))

    hk = HeavyKeeper(k=k, width=counters // 4, depth=4, seed=1)
    hk.update_many(stream)
    results.append(evaluate("HeavyKeeper", hk, stream, k))

    return results


def bias_study(
    runs: int = 24,
    distinct: int = 5_000,
    length: int = 60_000,
    counters: int = 100,
    band: Tuple[int, int] = (40, 140),
) -> Dict[str, Tuple[float, float]]:
    """Measure Space-Saving's bias against its unbiased variant, across runs.

    Unbiasedness is a statement about an *expectation*, so a single run cannot
    demonstrate it: the estimator's variance is far larger than its bias. This
    repeats the experiment over independent streams and reports the mean bias
    with its standard error, which is the only way to tell the two apart -- or,
    as it turns out here, to establish that they cannot be told apart on this
    workload.

    The band is deliberately taken from the *middle* of the frequency
    distribution. The genuine top items are never evicted, so their counts are
    exact under both schemes and show no bias at all; items far down the tail
    are never retained. The eviction boundary is the only place the difference
    could appear.

    Args:
        runs: Number of independent repetitions.
        distinct: Distinct items per stream.
        length: Stream length.
        counters: Counters given to each structure.
        band: Half-open rank range to score, by true frequency.

    Returns:
        ``{name: (mean_bias, standard_error)}``.
    """
    import statistics

    samples: Dict[str, List[float]] = {"SpaceSaving": [], "UnbiasedSpaceSaving": []}
    lo, hi = band
    for seed in range(runs):
        stream = zipf_stream(distinct, length, 1.05, seed=seed)
        truth: Dict[Item, int] = {}
        for item in stream:
            truth[item] = truth.get(item, 0) + 1
        ranked = [i for i, _ in sorted(truth.items(), key=lambda kv: -kv[1])][lo:hi]
        if not ranked:
            continue

        ss = StreamSummary(k=counters)
        ss.update_many(stream)
        uss = UnbiasedSpaceSaving(k=counters, seed=seed)
        uss.update_many(stream)
        for name, summary in (("SpaceSaving", ss), ("UnbiasedSpaceSaving", uss)):
            errors = [(summary.estimate(i).count - truth[i]) / truth[i] for i in ranked]
            samples[name].append(sum(errors) / len(errors))

    return {
        name: (
            statistics.mean(values),
            statistics.stdev(values) / len(values) ** 0.5 if len(values) > 1 else 0.0,
        )
        for name, values in samples.items()
        if values
    }


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import time

    print("Zipf(1.1) stream: 500,000 elements over 20,000 distinct items")
    print("Each structure gets 200 counters; recovering the true top 50.\n")
    for report in compare():
        print(f"  {report}")

    print("\nUpdate throughput (1,000,000 elements, 200 counters):")
    stream = zipf_stream(20_000, 1_000_000, 1.1, seed=2)
    for name, factory in [
        ("MisraGries", lambda: MisraGries(k=200)),
        ("StreamSummary", lambda: StreamSummary(k=200)),
        ("UnbiasedSpaceSaving", lambda: UnbiasedSpaceSaving(k=200, seed=3)),
        ("HeavyKeeper", lambda: HeavyKeeper(k=50, width=50, depth=4, seed=3)),
    ]:
        summary = factory()
        start = time.perf_counter()
        summary.update_many(stream)
        elapsed = time.perf_counter() - start
        print(f"  {name:<24}{elapsed:6.2f}s  ({len(stream) / elapsed / 1e6:5.2f}M/s)")

    print("\nHeavyKeeper vs Space-Saving at a 64-cell budget, by stream skew:")
    print(f"  {'skew':>6}{'HeavyKeeper':>14}{'Space-Saving':>15}{'HK wins':>10}")
    for skew in (1.0, 1.1, 1.3):
        hk_recalls, ss_recalls = [], []
        for seed in range(8):
            sample = zipf_stream(5_000, 100_000, skew, seed=seed)
            hk = HeavyKeeper(k=16, width=16, depth=4, seed=seed)
            hk.update_many(sample)
            ss = StreamSummary(k=64)
            ss.update_many(sample)
            hk_recalls.append(evaluate("hk", hk, sample, 16).recall)
            ss_recalls.append(evaluate("ss", ss, sample, 16).recall)
        wins = sum(a >= b for a, b in zip(hk_recalls, ss_recalls))
        print(
            f"  {skew:>6.1f}{sum(hk_recalls) / len(hk_recalls):>13.3f}"
            f"{sum(ss_recalls) / len(ss_recalls):>15.3f}{wins:>7} of 8"
        )
    print("  Decay helps exactly where the tail is heaviest relative to the head.")

    print("\nIs Unbiased Space-Saving measurably less biased? (24 independent runs,")
    print("scored on the eviction boundary, where the difference could show up)")
    for name, (mean, stderr) in bias_study().items():
        verdict = "indistinguishable from 0" if abs(mean) < 2 * stderr else "biased"
        print(f"  {name:<22}{mean:+7.2%} +/- {stderr:.2%} (stderr)  -- {verdict}")
    print("  The theoretical difference is real; the estimator variance on this")
    print("  workload is an order of magnitude larger, so it does not show up.")

    print("\nMergeability -- only Misra-Gries has it:")
    left, right = MisraGries(k=50), MisraGries(k=50)
    half = len(stream) // 2
    left.update_many(stream[:half])
    right.update_many(stream[half:])
    merged = left.merge(right)
    direct = MisraGries(k=50)
    direct.update_many(stream)
    merged_top = [e.item for e in merged.top_k(10)]
    direct_top = [e.item for e in direct.top_k(10)]
    overlap = len(set(merged_top) & set(direct_top))
    print(f"  merged top-10 vs single-pass top-10: {overlap}/10 items in common")
