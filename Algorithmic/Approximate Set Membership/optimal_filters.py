"""Space-optimal approximate membership query (AMQ) filters.

The classic answer to "is x in S?" with a small error budget is a Bloom filter
(see :mod:`bloom`). Bloom filters are *not* optimal: they need
``1.44 * log2(1/eps)`` bits per key, a 44% overhead over the information
theoretic lower bound of ``log2(1/eps)`` bits. This module implements the
structures that close most of that gap, plus the one that is fastest, plus the
one that supports deletion, so the trade-off can be measured rather than
assumed.

=================================  ==============  =============  ===========
Structure                          Bits/key @ 1/256  Deletes?      Probes
=================================  ==============  =============  ===========
Information-theoretic lower bound  8.00            --             --
:class:`HomogeneousRibbonFilter`   ~8.4            no (static)    1 window
:class:`BinaryFuse8Filter`         ~9.0            no (static)    3 (adjacent)
Classic Bloom (``bloom.py``)       ~11.5           no             k = 8
:class:`BlockedBloomFilter`        ~12-14          no             1 cache line
:class:`CuckooFilter`              ~14.7           yes            2 buckets
=================================  ==============  =============  ===========

See ``OPTIMAL.md`` in this directory for the full analysis, the lower bound
argument, and the reasoning behind each of these numbers.

All filters here are keyed on 64-bit integers. Use :func:`hash_bytes` to map
arbitrary objects into that space; doing the conversion in one place keeps the
"two inputs collided in 64 bits" failure mode explicit instead of hidden inside
each structure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

MASK64 = (1 << 64) - 1

__all__ = [
    "MASK64",
    "splitmix64",
    "mix",
    "mulhi",
    "hash_bytes",
    "lower_bound_bits_per_key",
    "BlockedBloomFilter",
    "BinaryFuse8Filter",
    "HomogeneousRibbonFilter",
    "CuckooFilter",
    "FilterReport",
    "measure",
]


# --------------------------------------------------------------------------
# Hashing primitives
# --------------------------------------------------------------------------


def splitmix64(z: int) -> int:
    """SplitMix64 finalizer: a strong 64-bit avalanche in three rounds.

    Args:
        z: Any integer; only the low 64 bits matter.

    Returns:
        A well-mixed 64-bit integer.
    """
    z = (z + 0x9E3779B97F4A7C15) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return z ^ (z >> 31)


def mix(key: int, seed: int) -> int:
    """Seeded 64-bit mixing of ``key``; the single entropy source per key."""
    return splitmix64((key + seed) & MASK64)


def mulhi(a: int, b: int) -> int:
    """High 64 bits of a 64x64 product.

    ``mulhi(h, n)`` maps a uniform 64-bit ``h`` to a near-uniform value in
    ``[0, n)``. It is both faster and better distributed than ``h % n`` when
    ``n`` is not a power of two, because it uses the *high* bits of the hash.
    """
    return ((a & MASK64) * (b & MASK64)) >> 64


def hash_bytes(data: bytes) -> int:
    """Map an arbitrary byte string to a 64-bit key.

    A multiply-xor accumulator with a SplitMix64 avalanche. Not cryptographic:
    an adversary who can choose inputs can force collisions. For adversarial
    workloads substitute a keyed hash (``siphash``); see ``OPTIMAL.md``.

    Args:
        data: The bytes to hash.

    Returns:
        A 64-bit integer key.
    """
    acc = 0x27D4EB2F165667C5
    n = len(data)
    full = n - (n % 8)
    for i in range(0, full, 8):
        word = int.from_bytes(data[i : i + 8], "little")
        acc = (acc ^ word) * 0x9E3779B97F4A7C15 & MASK64
        acc = ((acc << 31) | (acc >> 33)) & MASK64
    if full != n:
        acc = (
            acc ^ int.from_bytes(data[full:], "little")
        ) * 0xFF51AFD7ED558CCD & MASK64
    return splitmix64(acc ^ n)


def _key_of(item: object) -> int:
    """Coerce ``item`` to a 64-bit key: ints pass through, everything else hashes."""
    if isinstance(item, int) and not isinstance(item, bool):
        return item & MASK64
    if isinstance(item, bytes):
        return hash_bytes(item)
    if isinstance(item, str):
        return hash_bytes(item.encode("utf-8"))
    return hash_bytes(repr(item).encode("utf-8"))


class _Rng:
    """Deterministic xorshift64, so every construction in this module is reproducible."""

    __slots__ = ("state",)

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK64 or 0x9E3779B97F4A7C15

    def next(self) -> int:
        """Return the next 64-bit pseudo-random value."""
        x = self.state
        x ^= (x << 13) & MASK64
        x ^= x >> 7
        x ^= (x << 17) & MASK64
        self.state = x
        return x


def lower_bound_bits_per_key(eps: float) -> float:
    """Information-theoretic lower bound in bits per key for false positive rate ``eps``.

    Carter et al. (1978): any structure that answers membership for an ``n``
    element subset of a large universe with one-sided error ``eps`` must use at
    least ``n * log2(1/eps)`` bits. Every filter below is measured against this.
    """
    if not 0.0 < eps < 1.0:
        raise ValueError("eps must lie strictly between 0 and 1")
    return math.log2(1.0 / eps)


# --------------------------------------------------------------------------
# Blocked Bloom filter -- the speed-optimal point
# --------------------------------------------------------------------------


class BlockedBloomFilter:
    """Cache-line blocked Bloom filter: every query touches exactly one block.

    A classic Bloom filter with ``k`` hash functions performs ``k`` independent
    random probes, which is ``k`` cache misses. A blocked Bloom filter picks one
    512-bit block (one cache line on x86-64/ARM64) and sets all ``k`` bits
    inside it, so a query costs a single miss.

    The price is space: confining ``k`` bits to one block makes the per-block
    load uneven (some blocks receive more keys than average), which raises the
    false positive rate for a given size. Budget roughly 20-30% more memory than
    a classic Bloom filter for the same ``eps``.

    This is the right choice when the working set does not fit in cache and
    throughput dominates; it is the wrong choice when memory is the constraint,
    in which case use :class:`HomogeneousRibbonFilter` or
    :class:`BinaryFuse8Filter`.
    """

    BLOCK_BITS = 512
    BLOCK_BYTES = 64

    def __init__(
        self, capacity: int, false_positive_rate: float = 1 / 256, seed: int = 0x5EED
    ) -> None:
        """Size the filter for ``capacity`` keys at the requested error rate.

        Args:
            capacity: Expected number of distinct keys.
            false_positive_rate: Target ``eps``.
            seed: Hash seed.
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        eps = false_positive_rate
        if not 0.0 < eps < 1.0:
            raise ValueError("false_positive_rate must lie strictly between 0 and 1")

        self.capacity = capacity
        self.false_positive_rate = eps
        self.seed = seed & MASK64
        # Classic Bloom sizing, then a blocking surcharge for the uneven
        # per-block load. 1.30 is the usual empirical figure for 512-bit blocks.
        bits_classic = max(1.0, -capacity * math.log(eps) / (math.log(2) ** 2))
        self.hash_count = max(
            1, min(16, round(bits_classic / max(capacity, 1) * math.log(2)))
        )
        n_blocks = max(1, math.ceil(bits_classic * 1.30 / self.BLOCK_BITS))
        self.block_count = n_blocks
        self.data = bytearray(n_blocks * self.BLOCK_BYTES)
        self.element_count = 0

    def _block_and_pattern(self, key: int) -> tuple[int, int]:
        """Return the byte offset of the block and the 512-bit pattern for ``key``."""
        h = mix(key, self.seed)
        block = mulhi(h, self.block_count)
        # Derive k in-block positions from one 64-bit hash by rehashing. Using
        # disjoint bit-slices of a single hash would be cheaper but correlates
        # the positions once k * 9 > 64.
        pattern = 0
        h2 = splitmix64(h ^ 0xA5A5A5A5A5A5A5A5)
        for _ in range(self.hash_count):
            pattern |= 1 << (h2 & (self.BLOCK_BITS - 1))
            h2 = splitmix64(h2)
        return block * self.BLOCK_BYTES, pattern

    def add(self, item: object) -> None:
        """Insert ``item``."""
        off, pattern = self._block_and_pattern(_key_of(item))
        end = off + self.BLOCK_BYTES
        word = int.from_bytes(self.data[off:end], "little") | pattern
        self.data[off:end] = word.to_bytes(self.BLOCK_BYTES, "little")
        self.element_count += 1

    def contains(self, item: object) -> bool:
        """Return ``True`` if ``item`` is probably present, ``False`` if definitely absent."""
        off, pattern = self._block_and_pattern(_key_of(item))
        word = int.from_bytes(self.data[off : off + self.BLOCK_BYTES], "little")
        return word & pattern == pattern

    __contains__ = contains

    def bits(self) -> int:
        """Total size of the filter in bits."""
        return len(self.data) * 8

    def bits_per_key(self) -> float:
        """Bits of storage per inserted key."""
        return self.bits() / self.element_count if self.element_count else 0.0


# --------------------------------------------------------------------------
# Binary fuse filter -- the practical default for static sets
# --------------------------------------------------------------------------


class FuseConstructionError(RuntimeError):
    """Raised when peeling fails for every seed -- almost always duplicate keys."""


class BinaryFuse8Filter:
    """Binary fuse filter with 8-bit fingerprints (Graf & Lemire, ACM JEA 2022).

    Each key ``x`` maps to three slots of a fingerprint array and to an 8-bit
    fingerprint ``f(x)``, and the array is built so that::

        F[h0(x)] ^ F[h1(x)] ^ F[h2(x)] == f(x)   for every key x

    Membership is exactly that equation, so a non-key passes with probability
    ``2^-8``. There are no false negatives, and unlike a Bloom filter the cost
    is three *adjacent-segment* probes rather than eight scattered ones.

    Building the array means solving a sparse system of XOR equations. That is
    done by **peeling**: repeatedly find a slot touched by exactly one remaining
    key, record it, and remove that key. Assigning values in reverse peeling
    order guarantees each key gets a slot that no later assignment disturbs.

    The "fuse" geometry -- ``h0`` in segment ``s``, ``h1`` in ``s+1``, ``h2`` in
    ``s+2`` -- is what makes this better than the earlier xor filter. Confining
    the probes to a narrow window improves locality *and* lowers the peeling
    threshold, cutting space from ~9.84 bits/key (xor) to ~9.0.

    The structure is **static**: all keys must be known at construction time.
    """

    ARITY = 3
    MAX_SEGMENT_LENGTH = 1 << 18
    MAX_ATTEMPTS = 100

    def __init__(self, keys: Iterable[object], seed: int = 0x726F6E64) -> None:
        """Build a filter over ``keys``.

        Args:
            keys: The keys to store. Must be **distinct** after conversion to
                64-bit; duplicates hash to identical slot triples under every
                seed, so no seed can peel them.
            seed: Starting hash seed. Retries derive deterministically from it.

        Raises:
            FuseConstructionError: If peeling failed for ``MAX_ATTEMPTS`` seeds.
        """
        key_list = [_key_of(k) for k in keys]
        self.length = len(key_list)
        self.seed = seed & MASK64

        size = self.length
        segment_length = self._segment_length(size)
        size_factor = self._size_factor(size)
        capacity = 0 if size <= 1 else round(size * size_factor)

        init_segments = max(1, -(-capacity // segment_length) - (self.ARITY - 1))
        array_length = (init_segments + self.ARITY - 1) * segment_length
        segments = -(-array_length // segment_length)
        segments = segments - (self.ARITY - 1) if segments >= self.ARITY - 1 else 0
        array_length = (segments + self.ARITY - 1) * segment_length

        self.segment_length = segment_length
        self.segment_length_mask = segment_length - 1
        self.segment_count_length = segments * segment_length
        self.fingerprints = bytearray(array_length)

        rng = _Rng(self.seed | 1)
        for _ in range(self.MAX_ATTEMPTS):
            if self._populate(key_list):
                return
            self.seed = rng.next()
        raise FuseConstructionError(
            f"peeling failed after {self.MAX_ATTEMPTS} seeds over {self.length} keys; "
            "the most likely cause is duplicate keys"
        )

    @classmethod
    def _segment_length(cls, size: int) -> int:
        """Empirical segment size; the constants come from the reference implementation."""
        if size <= 1:
            return 4
        exponent = int(math.floor(math.log(size) / math.log(3.33) + 2.25))
        exponent = min(max(exponent, 2), 31)
        return min(1 << exponent, cls.MAX_SEGMENT_LENGTH)

    @staticmethod
    def _size_factor(size: int) -> float:
        """Slots per key. Tends to 1.125; small sets need slack for finite-size effects."""
        if size <= 1:
            return 2.0
        return max(1.125, 0.875 + 0.25 * math.log(1_000_000) / math.log(size))

    def _slots(self, h: int) -> tuple[int, int, int]:
        """The three array positions for hash ``h``, one per consecutive segment."""
        h0 = mulhi(h, self.segment_count_length)
        h1 = h0 + self.segment_length
        h2 = h1 + self.segment_length
        h1 ^= (h >> 18) & self.segment_length_mask
        h2 ^= h & self.segment_length_mask
        return h0, h1, h2

    @staticmethod
    def _fingerprint(h: int) -> int:
        """The 8-bit value the three slots must XOR to."""
        return (h ^ (h >> 32)) & 0xFF

    def _populate(self, keys: Sequence[int]) -> bool:
        """One peeling attempt with the current seed. ``False`` if not peelable."""
        n = len(self.fingerprints)
        if not keys:
            return True

        # Per slot: how many un-peeled keys touch it, and the XOR of their full
        # hashes. When the count falls to 1 that XOR *is* the surviving key's
        # hash -- which is how the key is recovered without ever storing it.
        counts = bytearray(n)
        hash_xor = [0] * n
        seed = self.seed
        slots = self._slots

        for key in keys:
            h = mix(key, seed)
            for s in slots(h):
                if counts[s] < 255:
                    counts[s] += 1
                hash_xor[s] ^= h

        queue = [i for i in range(n) if counts[i] == 1]
        order: List[tuple[int, int]] = []
        push = queue.append
        pop = queue.pop

        while queue:
            slot = pop()
            if counts[slot] != 1:
                continue
            h = hash_xor[slot]
            order.append((h, slot))
            for s in slots(h):
                counts[s] -= 1
                hash_xor[s] ^= h
                if counts[s] == 1:
                    push(s)

        if len(order) != len(keys):
            return False

        # Assign in reverse peeling order: when a key is placed, every key
        # peeled before it is already placed, and nothing peeled after it
        # touches this slot, so the write cannot invalidate an earlier key.
        fp = self.fingerprints
        for i in range(n):
            fp[i] = 0
        for h, slot in reversed(order):
            value = self._fingerprint(h)
            for s in slots(h):
                if s != slot:
                    value ^= fp[s]
            fp[slot] = value
        return True

    def contains(self, item: object) -> bool:
        """Return ``True`` if ``item`` is probably present, ``False`` if definitely absent."""
        if not self.fingerprints:
            return False
        h = mix(_key_of(item), self.seed)
        h0, h1, h2 = self._slots(h)
        fp = self.fingerprints
        return fp[h0] ^ fp[h1] ^ fp[h2] == self._fingerprint(h)

    __contains__ = contains

    def __len__(self) -> int:
        return self.length

    def bits(self) -> int:
        """Total size of the filter in bits."""
        return len(self.fingerprints) * 8

    def bits_per_key(self) -> float:
        """Bits of storage per stored key. Compare against ``log2(1/eps) = 8``."""
        return self.bits() / self.length if self.length else 0.0


# --------------------------------------------------------------------------
# Homogeneous ribbon filter -- the space-optimal point
# --------------------------------------------------------------------------

# Expand an 8-bit selector into a 64-bit mask with 0xFF per selected byte. Used
# to turn a coefficient row into a byte mask over a 64-slot window in one step.
_BYTE_EXPAND = [
    sum(0xFF << (8 * b) for b in range(8) if (v >> b) & 1) for v in range(256)
]


class HomogeneousRibbonFilter:
    """Homogeneous ribbon filter (Dillinger, Hubschle-Schneider, Sanders, Walzer, 2021/2022).

    This is the closest practical structure to the information-theoretic lower
    bound: at ``r = 8`` result bits and 5% slack it stores a set in roughly
    8.4 bits per key, against a bound of 8.0 and Bloom's 11.5.

    **The idea.** Give each key ``x`` a start offset ``s(x)`` and a random
    ``w``-bit coefficient row ``c(x)`` (here ``w = 64``), and look for a table
    ``Z`` of ``m`` ``r``-bit words satisfying the *homogeneous* linear system
    over GF(2)::

        XOR over set bits j of c(x) of Z[s(x) + j]  ==  0    for every key x

    A query recomputes that XOR and reports membership iff it is zero. A
    non-key's row is essentially a fresh random vector, so it lands in the
    solution space with probability ``2^-r``.

    **Why it is small and why it never fails.** A homogeneous system is always
    consistent -- ``Z = 0`` is a solution -- so unlike the xor/fuse filters
    there is no construction failure and no seed retry. Storing only ``m``
    words with ``m`` barely above ``n`` is possible because the *only* overhead
    is the slack needed to keep the solution space non-trivial. Setting the free
    variables to random values (not zero) is what makes the filter work: the
    all-zero table would accept everything.

    **Why it is fast.** The non-zero coefficients of a key lie in a window of
    ``w`` consecutive slots -- the "ribbon" -- so both construction and queries
    touch one contiguous ``w``-byte span. Gaussian elimination stays inside the
    band, which is what makes an ``O(n * w / 64)`` word-parallel solve possible.

    **Choosing the parameters -- the part the literature buries.** The false
    positive rate is *not* simply ``2^-r``. A query is a guaranteed false
    positive whenever its coefficient row lies in the span of the key rows
    overlapping its window. A window of ``w`` slots is overlapped by about
    ``w / (1 + slack)`` key rows, leaving roughly ``slack * w`` free dimensions,
    so the excess error decays in the **product** ``slack * w`` -- not in either
    parameter alone. Measured over 40k keys at ``r = 8``:

    ========  =====  =========  ========  =============
    slack     w      slack * w  bits/key  fpp / 2^-8
    ========  =====  =========  ========  =============
    0.02      64     1.3        8.17      33.2  (broken)
    0.02      128    2.6        8.19       1.01
    0.02      256    5.1        8.21       0.96
    0.05      64     3.2        8.41       3.99  (bad)
    0.05      128    6.4        8.43       0.96
    0.10      64     6.4        8.81       0.90
    ========  =====  =========  ========  =============

    The cliff is sharp and sits near ``slack * w = 2.5``. The practical
    consequence is that **slack should be spent on width, not on slots**:
    widening the ribbon costs construction time but almost no memory, whereas
    adding slots costs memory linearly. The default configuration below --
    ``slack = 0.02`` with ``w = 256`` -- reaches 8.21 bits per key at the
    nominal error rate, i.e. **1.03x the information-theoretic lower bound**,
    against 1.44x for a Bloom filter.

    The structure is **static**: all keys must be known at construction time.
    """

    #: Empirical threshold for ``slack * width`` above which the excess false
    #: positive rate disappears. Measured cliff is near 2.5; 5 is the safety
    #: margin, and costs about 0.02 bits/key.
    WIDTH_SLACK_PRODUCT = 5.0

    @staticmethod
    def recommended_width(slack: float) -> int:
        """Smallest supported ribbon width whose ``slack * w`` keeps error near ``2^-r``.

        Rounded up to a power-of-two multiple of 64, since the word-parallel
        query path works a byte-window at a time.
        """
        if slack <= 0:
            return 1024
        target = HomogeneousRibbonFilter.WIDTH_SLACK_PRODUCT / slack
        width = 64
        while width < target and width < 1024:
            width *= 2
        return width

    def __init__(
        self,
        keys: Iterable[object],
        slack: float = 0.02,
        seed: int = 0x21BB07,
        width: Optional[int] = None,
    ) -> None:
        """Build a filter over ``keys``.

        Args:
            keys: The keys to store. Duplicates are harmless here (a repeated
                key yields a redundant equation, which elimination drops).
            slack: Fraction of extra slots beyond ``n``. Lower is smaller but
                raises the false positive rate; 0.02-0.10 is the useful range.
                Slack below zero ("overloading") is allowed and degrades
                gracefully rather than failing.
            seed: Hash seed.
            width: Ribbon width ``w`` in slots; must be a positive multiple of
                64. Defaults to :meth:`recommended_width` for the given slack.
                Wider ribbons cost construction time but cut the excess false
                positive rate exponentially.
        """
        if slack <= -1.0:
            raise ValueError("slack must be greater than -1")
        if width is None:
            width = self.recommended_width(slack)
        if width <= 0 or width % 64 != 0:
            raise ValueError("width must be a positive multiple of 64")
        self.width = width
        key_list = [_key_of(k) for k in keys]
        self.length = len(key_list)
        self.seed = seed & MASK64
        self.slack = slack

        # Need at least one full window plus a little headroom.
        self.m = max(
            self.width * 2, int(math.ceil(self.length * (1.0 + slack))) + self.width
        )

        # coeff[p] is the pivot equation whose leading term is slot p, stored as
        # a w-bit integer with bit 0 set. Zero means "no pivot here".
        coeff: List[int] = [0] * self.m
        for key in key_list:
            self._insert(coeff, key)

        self._back_substitute(coeff)

    def _row(self, key: int) -> tuple[int, int]:
        """Return ``(start, coefficients)`` for ``key``.

        ``start`` is uniform in ``[0, m - w]`` and the coefficient row is a
        random ``w``-bit value with bit 0 forced on, so the leading term is
        always at ``start``.
        """
        h = mix(key, self.seed)
        start = mulhi(h, self.m - self.width + 1)
        c = 0
        word = h
        for shift in range(0, self.width, 64):
            word = splitmix64(word ^ 0x9E3779B97F4A7C15)
            c |= word << shift
        return start, c | 1

    def _insert(self, coeff: List[int], key: int) -> None:
        """Fold one key's equation into the banded triangular system.

        This is incremental Gaussian elimination restricted to the band. Each
        iteration either claims an empty pivot row (done) or cancels against an
        existing one, which clears the leading bit and pushes ``start`` strictly
        forward -- so the loop runs at most ``w`` times.
        """
        start, c = self._row(key)
        while c:
            shift = (c & -c).bit_length() - 1
            start += shift
            c >>= shift
            existing = coeff[start]
            if existing == 0:
                coeff[start] = c
                return
            c ^= existing  # both have bit 0 set, so the leading term cancels
        # c == 0: the equation is a linear combination of earlier ones. In a
        # homogeneous system its right-hand side is 0 too, so it is redundant
        # and simply dropped -- this is why construction can never fail.

    def _back_substitute(self, coeff: List[int]) -> bytearray:
        """Solve the triangular system bottom-up, filling free slots at random.

        Free variables *must* be random. Zeroing them yields ``Z = 0``, which
        satisfies every equation and therefore reports every query as a member.
        """
        self.table = bytearray(self.m)
        rng = _Rng(self.seed ^ 0xD1B54A32D192ED03)
        for pos in range(self.m - 1, -1, -1):
            c = coeff[pos]
            if c == 0:
                self.table[pos] = rng.next() & 0xFF
            else:
                # Every term of this equation other than the pivot lies to the
                # right of pos, and is therefore already solved.
                self.table[pos] = self._select_xor(pos + 1, c >> 1)
        return self.table

    def _select_xor(self, start: int, c: int) -> int:
        """XOR of ``table[start + j]`` over the set bits ``j`` of ``c``.

        Rather than looping over ``w`` bits, this masks the whole ``w``-byte
        window at once and folds it with ``log2(w) + 3`` shift-XOR steps. It is
        the Python-specific trick that keeps the ribbon query competitive:
        big-integer operations run in C, per-bit Python loops do not.
        """
        window = int.from_bytes(self.table[start : start + self.width], "little")
        mask = 0
        rest = c
        shift = 0
        while rest:
            mask |= _BYTE_EXPAND[rest & 0xFF] << shift
            rest >>= 8
            shift += 64
        x = window & mask
        fold = self.width * 8 // 2
        while fold >= 8:
            x ^= x >> fold
            fold //= 2
        return x & 0xFF

    def contains(self, item: object) -> bool:
        """Return ``True`` if ``item`` is probably present, ``False`` if definitely absent."""
        start, c = self._row(_key_of(item))
        return self._select_xor(start, c) == 0

    __contains__ = contains

    def __len__(self) -> int:
        return self.length

    def bits(self) -> int:
        """Total size of the filter in bits."""
        return len(self.table) * 8

    def bits_per_key(self) -> float:
        """Bits of storage per stored key. Compare against ``log2(1/eps) = 8``."""
        return self.bits() / self.length if self.length else 0.0


# --------------------------------------------------------------------------
# Cuckoo filter -- the answer when the set changes
# --------------------------------------------------------------------------


class CuckooFilter:
    """Cuckoo filter (Fan, Andersen, Kaminsky, Mitzenmacher, CoNEXT 2014).

    The fuse and ribbon filters above solve a global linear system, so they are
    strictly static. When the set changes -- and in particular when keys must be
    *deleted* -- the cuckoo filter is the best of the practical options: it
    beats a counting Bloom filter on space for any ``eps`` below about 3%.

    Fingerprints are stored in a cuckoo hash table with two candidate buckets
    per key. The trick that makes it work without storing keys is **partial-key
    cuckoo hashing**: the alternate bucket is derived from the fingerprint
    alone, ``i2 = i1 XOR hash(f)``, so a displaced fingerprint can be relocated
    without knowing which key produced it.

    Deletion is only sound if the key was actually inserted; deleting a
    never-inserted key can remove a colliding fingerprint belonging to a real
    key and introduce a false *negative*. That is a property of the structure,
    not of this implementation.

    One subtlety that naive implementations get wrong: when the eviction chain
    gives up, it is still *holding* a fingerprint that has been removed from its
    bucket. Dropping it loses a key that was legitimately inserted earlier and
    silently introduces a false negative. This implementation parks it in a
    one-slot victim cache, as the original paper prescribes, so membership stays
    sound even after the table saturates.
    """

    BUCKET_SIZE = 4
    MAX_KICKS = 500

    def __init__(
        self,
        capacity: int,
        fingerprint_bits: int = 12,
        seed: int = 0xC0FFEE,
        load_factor: float = 0.94,
    ) -> None:
        """Size a filter for roughly ``capacity`` keys.

        Args:
            capacity: Expected number of keys.
            fingerprint_bits: Bits per fingerprint. The false positive rate is
                about ``2 * BUCKET_SIZE / 2^fingerprint_bits``, so 12 bits gives
                ~0.2% and 8 bits gives ~3%.
            seed: Hash seed.
            load_factor: Target occupancy; 0.94-0.95 is where 4-slot buckets
                start failing to insert.
        """
        if not 4 <= fingerprint_bits <= 32:
            raise ValueError("fingerprint_bits must lie in [4, 32]")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self.fingerprint_bits = fingerprint_bits
        self.fingerprint_mask = (1 << fingerprint_bits) - 1
        self.seed = seed & MASK64
        # Bucket count must be a power of two: the XOR trick that recovers the
        # alternate bucket is only an involution modulo a power of two.
        needed = max(1, math.ceil(max(capacity, 1) / (self.BUCKET_SIZE * load_factor)))
        self.bucket_count = 1 << max(1, (needed - 1).bit_length())
        self.buckets: List[List[int]] = [[] for _ in range(self.bucket_count)]
        self.element_count = 0
        # Holds the fingerprint orphaned by a failed eviction chain, plus one of
        # its two candidate buckets. Without it, saturation causes silent false
        # negatives.
        self._victim: Optional[tuple[int, int]] = None
        self._rng = _Rng(self.seed ^ 0x1234_5678_9ABC_DEF0)

    def _fingerprint_and_index(self, key: int) -> tuple[int, int]:
        """Return a non-zero fingerprint and the primary bucket index."""
        h = mix(key, self.seed)
        # 0 is reserved as "empty", so fold it away rather than biasing.
        f = (h & self.fingerprint_mask) or 1
        i1 = (h >> 32) & (self.bucket_count - 1)
        return f, i1

    def _alt_index(self, index: int, fingerprint: int) -> int:
        """The other candidate bucket, derived from the fingerprint alone."""
        return (index ^ splitmix64(fingerprint)) & (self.bucket_count - 1)

    def add(self, item: object) -> bool:
        """Insert ``item``.

        Returns:
            ``True`` on success. ``False`` means the table saturated: the
            eviction chain hit ``MAX_KICKS`` and the fingerprint it was holding
            went into the victim cache. Membership remains correct, but no
            further insertion will succeed and the filter should be rebuilt at
            a larger size.
        """
        if self._victim is not None:
            return False

        f, i1 = self._fingerprint_and_index(_key_of(item))
        i2 = self._alt_index(i1, f)
        for idx in (i1, i2):
            if len(self.buckets[idx]) < self.BUCKET_SIZE:
                self.buckets[idx].append(f)
                self.element_count += 1
                return True

        # Both candidates are full: evict a random occupant and re-home it.
        idx = i1 if self._rng.next() & 1 else i2
        for _ in range(self.MAX_KICKS):
            slot = self._rng.next() % self.BUCKET_SIZE
            f, self.buckets[idx][slot] = self.buckets[idx][slot], f
            idx = self._alt_index(idx, f)
            if len(self.buckets[idx]) < self.BUCKET_SIZE:
                self.buckets[idx].append(f)
                self.element_count += 1
                return True

        # Out of kicks while still holding `f`, which no longer lives in any
        # bucket. Park it rather than drop it.
        self._victim = (f, idx)
        self.element_count += 1
        return False

    def contains(self, item: object) -> bool:
        """Return ``True`` if ``item`` is probably present, ``False`` if definitely absent."""
        f, i1 = self._fingerprint_and_index(_key_of(item))
        i2 = self._alt_index(i1, f)
        if self._victim is not None:
            vf, vi = self._victim
            if vf == f and vi in (i1, i2):
                return True
        return f in self.buckets[i1] or f in self.buckets[i2]

    __contains__ = contains

    def remove(self, item: object) -> bool:
        """Delete one copy of ``item``.

        Only sound for keys that were actually inserted -- see the class
        docstring.

        Returns:
            ``True`` if a matching fingerprint was removed.
        """
        f, i1 = self._fingerprint_and_index(_key_of(item))
        i2 = self._alt_index(i1, f)
        for idx in (i1, i2):
            bucket = self.buckets[idx]
            if f in bucket:
                bucket.remove(f)
                self.element_count -= 1
                return True
        if self._victim is not None:
            vf, vi = self._victim
            if vf == f and vi in (i1, i2):
                self._victim = None
                self.element_count -= 1
                return True
        return False

    def __len__(self) -> int:
        return self.element_count

    def bits(self) -> int:
        """Total size of the filter in bits, counting reserved slots."""
        return self.bucket_count * self.BUCKET_SIZE * self.fingerprint_bits

    def bits_per_key(self) -> float:
        """Bits of storage per stored key."""
        return self.bits() / self.element_count if self.element_count else 0.0


# --------------------------------------------------------------------------
# Measurement harness
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FilterReport:
    """Measured properties of one filter over one key set."""

    name: str
    keys: int
    bits_per_key: float
    measured_fpp: float
    lower_bound_bits_per_key: float
    false_negatives: int

    @property
    def space_overhead(self) -> float:
        """Ratio of actual to information-theoretically necessary space.

        1.00 would mean optimal. Bloom filters sit at 1.44 by construction.
        """
        if self.lower_bound_bits_per_key <= 0:
            return float("nan")
        return self.bits_per_key / self.lower_bound_bits_per_key

    def __str__(self) -> str:
        return (
            f"{self.name:<26} {self.bits_per_key:6.2f} bits/key "
            f"(x{self.space_overhead:4.2f} of optimal)  "
            f"fpp={self.measured_fpp:8.5f}  false negatives={self.false_negatives}"
        )


def measure(
    name: str,
    filt: object,
    members: Sequence[int],
    non_members: Sequence[int],
    target_fpp: Optional[float] = None,
) -> FilterReport:
    """Empirically measure a filter's false positive rate and space efficiency.

    Args:
        name: Label for the report.
        filt: Any object exposing ``contains`` and ``bits_per_key``.
        members: Keys that were inserted; used to check for false negatives.
        non_members: Keys that were **not** inserted; used to estimate ``eps``.
        target_fpp: Error rate to compare space against. Defaults to the
            measured rate, which is the honest comparison when the structure
            picks its own ``eps``.

    Returns:
        A :class:`FilterReport`.
    """
    contains = filt.contains  # type: ignore[attr-defined]
    false_negatives = sum(1 for k in members if not contains(k))
    hits = sum(1 for k in non_members if contains(k))
    fpp = hits / len(non_members) if non_members else 0.0
    eps = target_fpp if target_fpp is not None else max(fpp, 1e-9)
    return FilterReport(
        name=name,
        keys=len(members),
        bits_per_key=filt.bits_per_key(),  # type: ignore[attr-defined]
        measured_fpp=fpp,
        lower_bound_bits_per_key=lower_bound_bits_per_key(min(eps, 0.999999)),
        false_negatives=false_negatives,
    )


def _demo(n: int = 200_000, trials: int = 200_000) -> List[FilterReport]:
    """Build every filter over the same key set and report space vs. accuracy."""
    members = [splitmix64(i) for i in range(n)]
    non_members = [splitmix64(i) for i in range(1 << 40, (1 << 40) + trials)]
    # Every filter is scored against the lower bound at *its own measured*
    # error rate, which is the only fair comparison when each structure
    # lands on a slightly different eps.
    target = 1 / 256

    reports = []

    blocked = BlockedBloomFilter(capacity=n, false_positive_rate=target)
    for k in members:
        blocked.add(k)
    reports.append(measure("BlockedBloomFilter", blocked, members, non_members))

    fuse = BinaryFuse8Filter(members)
    reports.append(measure("BinaryFuse8Filter", fuse, members, non_members))

    ribbon = HomogeneousRibbonFilter(members, slack=0.02)
    reports.append(measure("HomogeneousRibbonFilter", ribbon, members, non_members))

    cuckoo = CuckooFilter(capacity=n, fingerprint_bits=12)
    for k in members:
        cuckoo.add(k)
    reports.append(measure("CuckooFilter(12b)", cuckoo, members, non_members))

    return reports


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    print(
        f"Lower bound at eps=1/256: {lower_bound_bits_per_key(1 / 256):.2f} bits/key\n"
    )
    for report in _demo():
        print(report)
