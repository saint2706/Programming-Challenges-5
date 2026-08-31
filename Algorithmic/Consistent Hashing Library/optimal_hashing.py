"""Consistent hashing: the algorithms that superseded the hash ring.

The hash ring (Karger et al., 1997) is what "consistent hashing" usually means,
and it has been the wrong default for about a decade. To get acceptable load
balance it needs 100-1000 *virtual nodes* per physical node, which costs memory
linear in that product, makes every membership change an `O(V*N log(V*N))`
re-sort, and *still* leaves a load imbalance of several percent.

Four algorithms do better, each giving up something different:

=====================  =========  ==========  ===========  ==================
Algorithm              Lookup     Memory      Balance      Arbitrary removal?
=====================  =========  ==========  ===========  ==================
:class:`HashRing`      O(log VN)  O(V*N)      ~1.10x       yes
:class:`JumpHash`      O(ln N)    **zero**    **perfect**  no (tail only)
:class:`RendezvousHash` O(N)      O(N)        near-perfect yes, weighted
:class:`MaglevHash`    **O(1)**   O(M)        near-perfect yes, but not minimal
:class:`AnchorHash`    O(1) amort O(capacity) near-perfect **yes**
=====================  =========  ==========  ===========  ==================

*Minimal disruption* -- the property the whole field exists for -- means that
removing a node moves **only that node's keys**, and no others. Note that this
is not the same as "moves 1/N of the keys": a node holding less than its share
moves fewer than 1/N while still shuffling other nodes' keys around. The only
sound test is that no surviving node lost a key, which is what :func:`compare`
measures. Every algorithm here passes it except Maglev, which is the
interesting exception: it is deployed at enormous scale precisely where
disruption is cheap.

Use :func:`compare` to measure balance and disruption rather than trusting the
table. See ``OPTIMAL.md`` for the analysis.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Callable, Dict, Hashable, List, Optional, Sequence, Tuple

MASK64 = (1 << 64) - 1

__all__ = [
    "HashRing",
    "JumpHash",
    "RendezvousHash",
    "MaglevHash",
    "AnchorHash",
    "Report",
    "balance",
    "disruption",
    "compare",
]


def _mix(value: int, seed: int = 0) -> int:
    """SplitMix64 finalizer, seeded. The single hash primitive for this module."""
    z = (value + seed + 0x9E3779B97F4A7C15) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return z ^ (z >> 31)


def _hash_key(key: Hashable, seed: int = 0) -> int:
    """Map an arbitrary key to a well-distributed 64-bit integer."""
    if isinstance(key, int) and not isinstance(key, bool):
        return _mix(key & MASK64, seed)
    if isinstance(key, bytes):
        raw = key
    elif isinstance(key, str):
        raw = key.encode("utf-8")
    else:
        raw = repr(key).encode("utf-8")
    acc = 0xCBF29CE484222325
    for chunk in range(0, len(raw), 8):
        acc = _mix(acc ^ int.from_bytes(raw[chunk : chunk + 8], "little"))
    return _mix(acc ^ len(raw), seed)


# --------------------------------------------------------------------------
# The baseline: hash ring with virtual nodes
# --------------------------------------------------------------------------


class HashRing:
    """Karger's consistent hash ring with virtual nodes.

    Nodes and keys are hashed onto the same circular space; a key belongs to the
    first node clockwise from it. Adding a node steals only the arc between it
    and its predecessor, which is the minimal-disruption property.

    Without virtual nodes the arcs have wildly uneven lengths -- the largest is
    `O(log N / N)` of the circle rather than `1/N` -- so each physical node is
    placed at `V` points to average the variance away. `V = 100` to `1000` is
    the usual range, and that multiplier is the algorithm's real cost: memory is
    `O(V*N)`, and every membership change re-sorts the whole structure.

    Included as the baseline the others are measured against.
    """

    def __init__(
        self, nodes: Optional[Sequence[str]] = None, virtual_nodes: int = 160
    ) -> None:
        """Create a ring.

        Args:
            nodes: Initial node names.
            virtual_nodes: Points on the circle per physical node. Higher gives
                better balance and costs proportional memory.

        Raises:
            ValueError: If ``virtual_nodes`` is not positive.
        """
        if virtual_nodes <= 0:
            raise ValueError("virtual_nodes must be positive")
        self.virtual_nodes = virtual_nodes
        self._hashes: List[int] = []
        self._owners: List[str] = []
        self._nodes: List[str] = []
        for node in nodes or ():
            self.add(node)

    @property
    def nodes(self) -> List[str]:
        """The physical nodes currently in the ring."""
        return list(self._nodes)

    def add(self, node: str) -> None:
        """Add a physical node, placing ``virtual_nodes`` points on the circle."""
        if node in self._nodes:
            return
        self._nodes.append(node)
        for replica in range(self.virtual_nodes):
            point = _hash_key(f"{node}#{replica}")
            position = bisect.bisect(self._hashes, point)
            self._hashes.insert(position, point)
            self._owners.insert(position, node)

    def remove(self, node: str) -> None:
        """Remove a physical node and all of its points."""
        if node not in self._nodes:
            return
        self._nodes.remove(node)
        kept = [(h, o) for h, o in zip(self._hashes, self._owners) if o != node]
        self._hashes = [h for h, _ in kept]
        self._owners = [o for _, o in kept]

    def lookup(self, key: Hashable) -> Optional[str]:
        """Return the node owning ``key``, or ``None`` if the ring is empty."""
        if not self._hashes:
            return None
        position = bisect.bisect(self._hashes, _hash_key(key))
        return self._owners[position % len(self._owners)]


# --------------------------------------------------------------------------
# Jump consistent hash: zero memory, perfect balance
# --------------------------------------------------------------------------


class JumpHash:
    """Jump consistent hash (Lamping & Veach, 2014).

    Remarkable for what it does *not* have: no data structure at all. Twenty
    lines of arithmetic map a key and a bucket count to a bucket, with perfect
    balance and minimal disruption, in `O(ln N)` time and **zero bytes** of
    state.

    **The idea.** Ask, for a key, at which bucket counts its assignment would
    change. Going from `n` to `n+1` buckets, a key must move to the new bucket
    with probability exactly `1/(n+1)` and stay otherwise. So instead of
    simulating every step, *sample the jumps*: draw the next `n` at which a move
    happens directly from the geometric distribution implied by that
    probability. Only `O(ln N)` jumps occur, so the loop is short.

    **The catch, and it is a real one.** Buckets are the integers `0..N-1`, and
    the only membership change the guarantee covers is growing or shrinking at
    the **tail**. Removing bucket 3 from a set of 10 is not expressible: you can
    only go to 9 buckets, which renumbers everything. That makes it ideal for
    sharding a dataset over a resizable pool, and unusable for a load balancer
    over named servers that fail individually.

    Example:
        >>> JumpHash(10).lookup(1234) < 10
        True
    """

    def __init__(self, buckets: int) -> None:
        """Create a mapping onto ``buckets`` buckets.

        Raises:
            ValueError: If ``buckets`` is not positive.
        """
        if buckets <= 0:
            raise ValueError("buckets must be positive")
        self.buckets = buckets

    def lookup(self, key: Hashable) -> int:
        """Return the bucket index in ``[0, buckets)`` for ``key``."""
        return self.lookup_in(_hash_key(key), self.buckets)

    @staticmethod
    def lookup_in(key_hash: int, buckets: int) -> int:
        """Assign a 64-bit key hash to one of ``buckets`` buckets.

        Args:
            key_hash: A well-distributed 64-bit integer.
            buckets: Number of buckets, at least 1.

        Returns:
            A bucket index in ``[0, buckets)``.
        """
        state = key_hash & MASK64
        chosen = -1
        candidate = 0
        while candidate < buckets:
            chosen = candidate
            # A 64-bit LCG supplies the uniform variate for each jump.
            state = (state * 2862933555777941757 + 1) & MASK64
            candidate = int((chosen + 1) * ((1 << 31) / float((state >> 33) + 1)))
        return chosen


# --------------------------------------------------------------------------
# Rendezvous hashing: weights and arbitrary removal
# --------------------------------------------------------------------------


class RendezvousHash:
    """Rendezvous / highest-random-weight hashing (Thaler & Ravishankar, 1998).

    Score every node against the key and take the highest. Minimal disruption
    falls out immediately: removing a node only affects keys whose maximum it
    was, and adding one only affects keys where it becomes the new maximum. No
    virtual nodes, no ring, no state beyond the node list.

    Its distinguishing feature is **native weighting**. Scaling the score by
    `-weight / ln(u)`, where `u` is the node's hash mapped into `(0, 1)`, makes
    the probability of winning exactly proportional to the weight -- an exact
    result, not an approximation, and something the ring can only imitate by
    handing bigger nodes more virtual nodes.

    The cost is `O(N)` per lookup. That is fine for tens of nodes and wrong for
    thousands; :class:`AnchorHash` keeps the same properties at `O(1)`.

    Example:
        >>> ring = RendezvousHash({"a": 1.0, "b": 3.0})
        >>> ring.lookup("some-key") in {"a", "b"}
        True
    """

    def __init__(
        self, nodes: Optional[Dict[str, float] | Sequence[str]] = None
    ) -> None:
        """Create a hasher.

        Args:
            nodes: Either a sequence of node names (all weight 1) or a mapping
                from node name to positive weight.

        Raises:
            ValueError: If any weight is not positive.
        """
        self._weights: Dict[str, float] = {}
        if nodes:
            if isinstance(nodes, dict):
                for node, weight in nodes.items():
                    self.add(node, weight)
            else:
                for node in nodes:
                    self.add(node)

    @property
    def nodes(self) -> List[str]:
        """The nodes currently in the set."""
        return list(self._weights)

    def add(self, node: str, weight: float = 1.0) -> None:
        """Add or re-weight a node.

        Raises:
            ValueError: If ``weight`` is not positive.
        """
        if weight <= 0:
            raise ValueError("weight must be positive")
        self._weights[node] = float(weight)

    def remove(self, node: str) -> None:
        """Remove a node. Removing an absent node is a no-op."""
        self._weights.pop(node, None)

    def lookup(self, key: Hashable) -> Optional[str]:
        """Return the highest-scoring node for ``key``, or ``None`` if empty."""
        ranked = self.rank(key, 1)
        return ranked[0] if ranked else None

    def rank(self, key: Hashable, count: int) -> List[str]:
        """Return the top ``count`` nodes for ``key``, best first.

        Useful for replication: the first `r` entries are a replica set that
        also degrades minimally when membership changes.
        """
        if not self._weights or count <= 0:
            return []
        key_hash = _hash_key(key)
        scored = []
        for node, weight in self._weights.items():
            # Map the node's hash into (0, 1), then -weight/ln(u). Larger weight
            # shifts the distribution up in exactly the right proportion.
            raw = _mix(key_hash, _hash_key(node)) / float(1 << 64)
            raw = min(max(raw, 1e-18), 1.0 - 1e-18)
            scored.append((-weight / math.log(raw), node))
        scored.sort(reverse=True)
        return [node for _, node in scored[:count]]


# --------------------------------------------------------------------------
# Maglev: O(1) lookup, and not minimally disruptive
# --------------------------------------------------------------------------


class MaglevHash:
    """Maglev hashing (Eisenbud et al., Google, NSDI 2016).

    Precompute a lookup table of `M` entries (`M` prime and much larger than the
    node count); a lookup is one array index. Each node proposes a permutation
    of the table positions, generated from an offset and a co-prime skip, and
    nodes take turns claiming their most-preferred unclaimed slot until the
    table is full. The result is near-perfect balance and genuinely `O(1)`
    lookups.

    **It does not have minimal disruption**, and this is the point worth
    understanding rather than treating as a defect. Rebuilding the table after a
    membership change reshuffles a fraction of *all* entries, not just the
    departed node's share. Google shipped it anyway because a Maglev load
    balancer fronts connection-tracked flows: existing connections are pinned by
    the connection table, so a remap only affects new ones. Disruption is cheap
    in that setting, and `O(1)` lookup at line rate is not.

    Use it when lookups dominate and remapping is cheap. Do not use it as a
    sharding function for stateful data, where remapping means moving bytes.
    """

    def __init__(
        self, nodes: Optional[Sequence[str]] = None, table_size: int = 65537
    ) -> None:
        """Create a Maglev table.

        Args:
            nodes: Initial node names.
            table_size: Number of table entries. Must be prime, and at least
                ~100x the node count for good balance.

        Raises:
            ValueError: If ``table_size`` is not prime.
        """
        if not _is_prime(table_size):
            raise ValueError(f"table_size {table_size} must be prime")
        self.table_size = table_size
        self._nodes: List[str] = list(nodes or ())
        self._table: List[str] = []
        self._rebuild()

    @property
    def nodes(self) -> List[str]:
        """The nodes currently in the table."""
        return list(self._nodes)

    def add(self, node: str) -> None:
        """Add a node and rebuild the table."""
        if node not in self._nodes:
            self._nodes.append(node)
            self._rebuild()

    def remove(self, node: str) -> None:
        """Remove a node and rebuild the table."""
        if node in self._nodes:
            self._nodes.remove(node)
            self._rebuild()

    def _rebuild(self) -> None:
        """Populate the lookup table by round-robin over each node's preferences."""
        count = len(self._nodes)
        if count == 0:
            self._table = []
            return
        size = self.table_size
        # Each node's preference list is offset + j*skip (mod size). Because
        # size is prime and skip is in [1, size), the sequence is a permutation.
        offsets = [_hash_key(node, 0xA1) % size for node in self._nodes]
        skips = [_hash_key(node, 0xB2) % (size - 1) + 1 for node in self._nodes]
        cursors = [0] * count

        table: List[Optional[str]] = [None] * size
        filled = 0
        while filled < size:
            for i, node in enumerate(self._nodes):
                candidate = (offsets[i] + cursors[i] * skips[i]) % size
                while table[candidate] is not None:
                    cursors[i] += 1
                    candidate = (offsets[i] + cursors[i] * skips[i]) % size
                table[candidate] = node
                cursors[i] += 1
                filled += 1
                if filled == size:
                    break
        self._table = [entry for entry in table if entry is not None]

    def lookup(self, key: Hashable) -> Optional[str]:
        """Return the node owning ``key`` in one array access."""
        if not self._table:
            return None
        return self._table[_hash_key(key) % self.table_size]


def _is_prime(value: int) -> bool:
    """Trial-division primality test; only used on the table size at construction."""
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    factor = 3
    while factor * factor <= value:
        if value % factor == 0:
            return False
        factor += 2
    return True


# --------------------------------------------------------------------------
# AnchorHash: everything at once
# --------------------------------------------------------------------------


class AnchorHash:
    """AnchorHash (Mendelson, Vargaftik, Barabash, Hay, Keslassy, Orda, 2019/2021).

    The algorithm that achieves all four properties simultaneously -- minimal
    disruption, near-perfect balance, `O(1)` expected lookup, and removal of
    **any** node, not just the last one. Nothing before it managed the set.

    **The idea.** Fix an *anchor* set of `a` bucket slots up front -- the maximum
    the cluster will ever reach. A key hashes into the anchor uniformly. If it
    lands on a working bucket, done. If it lands on a removed bucket `b`, the
    algorithm replays history: it re-hashes the key into the working set *as it
    was at the moment `b` was removed*, which it can do because `A[b]` records
    that set's size. Repeat until a working bucket is reached.

    That replay is why removal is minimally disruptive without any state per
    key: keys that never landed on `b` are untouched by definition, and keys
    that did are redistributed over exactly the set that existed when `b` left.
    The expected number of replay steps is `O(ln(a/N))`, so keeping the anchor
    within a small factor of the working set makes lookups effectively `O(1)`.

    The bookkeeping is three arrays -- ``A`` (size when removed, 0 if working),
    ``W``/``L`` (a swap-with-last working set with reverse index), and ``K``
    (each removed bucket's successor) -- all `O(a)` integers total, and updates
    are `O(1)`.

    Example:
        >>> anchor = AnchorHash(capacity=16, working=4)
        >>> anchor.remove(1)
        >>> anchor.lookup("key") in anchor.working_set
        True
    """

    def __init__(self, capacity: int, working: Optional[int] = None) -> None:
        """Create an anchor.

        Args:
            capacity: The anchor size ``a`` -- the largest the working set will
                ever be. Lookup cost grows with ``capacity / working``, so keep
                this within a small factor of the expected maximum.
            working: Number of initially working buckets, ``0..working-1``.
                Defaults to ``capacity``.

        Raises:
            ValueError: If the sizes are not positive or ``working`` exceeds
                ``capacity``.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if working is None:
            working = capacity
        if not 1 <= working <= capacity:
            raise ValueError("working must lie in [1, capacity]")

        self.capacity = capacity
        #: A[b] == 0 means bucket b is working; otherwise it is the size of the
        #: working set at the moment b was removed.
        self._a = [0] * capacity
        #: W[i] for i < N is the i-th working bucket; L is its inverse.
        self._w = list(range(capacity))
        self._l = list(range(capacity))
        #: K[b] is the bucket that took b's place when b was removed.
        self._k = list(range(capacity))
        self._removed: List[int] = []
        self._n = working

        # Buckets [working, capacity) start removed, most recent first.
        for bucket in range(capacity - 1, working - 1, -1):
            self._removed.append(bucket)
            self._a[bucket] = bucket

    @property
    def size(self) -> int:
        """Number of working buckets."""
        return self._n

    @property
    def working_set(self) -> List[int]:
        """The working buckets, in no particular order."""
        return sorted(self._w[: self._n])

    def remove(self, bucket: int) -> None:
        """Remove a working bucket.

        Raises:
            ValueError: If the bucket is out of range, already removed, or is
                the last working bucket.
        """
        if not 0 <= bucket < self.capacity:
            raise ValueError(f"bucket {bucket} outside anchor of size {self.capacity}")
        if self._a[bucket] != 0:
            raise ValueError(f"bucket {bucket} is already removed")
        if self._n <= 1:
            raise ValueError("cannot remove the last working bucket")

        self._removed.append(bucket)
        self._n -= 1
        # Record the working-set size at removal time. This single number is
        # what lets a later lookup reconstruct the historical set.
        self._a[bucket] = self._n
        last = self._w[self._n]
        self._w[self._l[bucket]] = last
        self._l[last] = self._l[bucket]
        self._k[bucket] = last

    def add(self) -> int:
        """Return a removed bucket to the working set, most recent first.

        Returns:
            The bucket that was restored.

        Raises:
            ValueError: If every bucket is already working.
        """
        if not self._removed:
            raise ValueError("all buckets are already working")
        bucket = self._removed.pop()
        self._a[bucket] = 0
        # Undo the swap-with-last performed at removal.
        self._l[self._w[self._n]] = self._n
        self._w[self._l[bucket]] = bucket
        self._k[bucket] = bucket
        self._n += 1
        return bucket

    def lookup(self, key: Hashable) -> int:
        """Return the working bucket owning ``key``.

        Complexity:
            `O(ln(capacity / size))` expected -- constant when the anchor is
            sized within a small factor of the working set.
        """
        key_hash = _hash_key(key)
        bucket = key_hash % self.capacity
        a, k = self._a, self._k
        while a[bucket] > 0:
            # `bucket` was removed when the working set had size a[bucket].
            # Re-hash into that historical set...
            candidate = _mix(key_hash, bucket) % a[bucket]
            # ...then walk forward past any bucket that had *already* been
            # removed by that time (a larger recorded size means an earlier
            # removal), following each one's recorded successor.
            while a[candidate] >= a[bucket]:
                candidate = k[candidate]
            bucket = candidate
        return bucket


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Report:
    """Measured properties of one algorithm."""

    name: str
    peak_to_mean: float
    moved: float
    victim_share: float
    unnecessary: float

    @property
    def is_minimally_disruptive(self) -> bool:
        """True if *only* the departing node's keys moved.

        This is the property the whole field exists for, and comparing total
        movement against ``1/N`` does not test it: a node holding less than its
        share can move fewer than ``1/N`` keys while still shuffling other
        nodes' keys around. The only sound test is that no key belonging to a
        surviving node moved.
        """
        return self.unnecessary == 0.0

    def __str__(self) -> str:
        verdict = "minimal" if self.is_minimally_disruptive else "NOT minimal"
        return (
            f"{self.name:<18} peak/mean={self.peak_to_mean:5.3f}  "
            f"moved={self.moved:6.2%}  "
            f"(departing node held {self.victim_share:5.2%}, "
            f"needlessly moved {self.unnecessary:6.3%}) {verdict}"
        )


def balance(assignments: Sequence[Hashable]) -> float:
    """Peak-to-mean load ratio. 1.00 is a perfectly even split."""
    if not assignments:
        return float("nan")
    counts: Dict[Hashable, int] = {}
    for owner in assignments:
        counts[owner] = counts.get(owner, 0) + 1
    mean = len(assignments) / len(counts)
    return max(counts.values()) / mean


def disruption(before: Sequence[Hashable], after: Sequence[Hashable]) -> float:
    """Fraction of keys whose owner changed between two assignments."""
    if not before:
        return 0.0
    moved = sum(1 for a, b in zip(before, after) if a != b)
    return moved / len(before)


def _report(name: str, before: Sequence, after: Sequence, victim: Hashable) -> Report:
    """Build a :class:`Report` from a before/after assignment pair."""
    total = len(before)
    victim_keys = sum(1 for owner in before if owner == victim)
    needless = sum(1 for a, b in zip(before, after) if a != b and a != victim)
    return Report(
        name=name,
        peak_to_mean=balance(before),
        moved=disruption(before, after),
        victim_share=victim_keys / total if total else 0.0,
        unnecessary=needless / total if total else 0.0,
    )


def compare(node_count: int = 20, key_count: int = 200_000) -> List[Report]:
    """Measure balance and removal disruption for every algorithm here.

    Removes one node from a cluster of ``node_count`` and reports both how many
    keys moved and -- the part that actually matters -- how many keys moved that
    did **not** belong to the departing node. That second number is zero exactly
    when the algorithm is minimally disruptive.

    Args:
        node_count: Cluster size.
        key_count: Number of keys to route.

    Returns:
        One :class:`Report` per algorithm.
    """
    keys = [f"key-{i}" for i in range(key_count)]
    names = [f"node-{i}" for i in range(node_count)]
    victim = names[node_count // 2]
    reports: List[Report] = []

    def measure(
        name: str, before_fn: Callable, after_fn: Callable, gone: Hashable
    ) -> None:
        before = [before_fn(k) for k in keys]
        after = [after_fn(k) for k in keys]
        reports.append(_report(name, before, after, gone))

    ring = HashRing(names, virtual_nodes=160)
    shrunk_ring = HashRing([n for n in names if n != victim], virtual_nodes=160)
    measure("HashRing(v=160)", ring.lookup, shrunk_ring.lookup, victim)

    # Jump hash can only shrink at the tail, so its "removal" is of the last
    # bucket -- which is exactly the limitation being documented.
    measure(
        "JumpHash (tail)",
        JumpHash(node_count).lookup,
        JumpHash(node_count - 1).lookup,
        node_count - 1,
    )

    rendezvous = RendezvousHash(names)
    shrunk_rendezvous = RendezvousHash([n for n in names if n != victim])
    measure("RendezvousHash", rendezvous.lookup, shrunk_rendezvous.lookup, victim)

    maglev = MaglevHash(names, table_size=65537)
    shrunk_maglev = MaglevHash([n for n in names if n != victim], table_size=65537)
    measure("MaglevHash", maglev.lookup, shrunk_maglev.lookup, victim)

    anchor = AnchorHash(capacity=node_count * 2, working=node_count)
    before = [anchor.lookup(k) for k in keys]
    anchor.remove(node_count // 2)
    after = [anchor.lookup(k) for k in keys]
    reports.append(_report("AnchorHash", before, after, node_count // 2))

    return reports


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import time

    print("Removing 1 node from a 20-node cluster, 200,000 keys.")
    print("Minimal disruption means no surviving node keeps losing keys.\n")
    for report in compare():
        print(f"  {report}")

    print("\nLookup throughput (20 nodes, 50,000 keys):")
    probes = [f"key-{i}" for i in range(50_000)]
    names = [f"node-{i}" for i in range(20)]
    structures: List[Tuple[str, Callable]] = [
        ("HashRing(v=160)", HashRing(names, virtual_nodes=160).lookup),
        ("JumpHash", JumpHash(20).lookup),
        ("RendezvousHash", RendezvousHash(names).lookup),
        ("MaglevHash", MaglevHash(names).lookup),
        ("AnchorHash", AnchorHash(capacity=40, working=20).lookup),
    ]
    for name, fn in structures:
        start = time.perf_counter()
        for key in probes:
            fn(key)
        elapsed = time.perf_counter() - start
        print(f"  {name:<18}{elapsed / len(probes) * 1e6:7.2f} us/lookup")
