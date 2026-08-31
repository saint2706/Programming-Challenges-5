"""Optimal approximate string matching: bit-parallel distance and automaton search.

Three separate problems hide under "approximate string matching", with three
different optimal answers:

1. **Distance between two strings.** The `O(mn)` DP is not optimal. Myers'
   bit-vector algorithm (1999) packs a whole DP column into machine words and
   runs in `O(n * ceil(m/w))`. Under SETH nothing does better than `O(n^(2-o(1)))`
   in general (Backurs & Indyk, STOC 2015), so word-parallelism is the entire
   remaining win -- and Myers extracts it. :func:`levenshtein`.

2. **Finding a pattern inside a long text, approximately.** The same bit
   trick with a different boundary condition gives every end position of an
   approximate occurrence in one pass. :func:`search`.

3. **Finding the near-matches of a query in a dictionary.** Neither of the above
   applies: comparing against every entry is `O(N)` distance computations. The
   right structure is a **trie traversed as a Levenshtein automaton**, sharing
   DP work across shared prefixes and pruning whole subtrees.
   :class:`FuzzyDictionary`. For very small edit distances,
   :class:`SymSpellIndex` trades a large index for near-constant lookups.

A note on Python specifically: Myers' algorithm is normally limited to patterns
of `w` characters (64) per machine word, and longer patterns need a blocked
multi-word implementation. Python's integers are arbitrary-precision, so the
"word" is as wide as the pattern -- the algorithm stays a single loop over the
text at any pattern length, with the bit arithmetic running in CPython's C
big-integer code. This is one of the rare cases where Python's number model is a
genuine algorithmic advantage rather than a tax.

See ``OPTIMAL.md`` for the analysis, the lower bound, and what BK-trees cost.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set, Tuple

__all__ = [
    "levenshtein",
    "levenshtein_dp",
    "bounded_levenshtein",
    "search",
    "Match",
    "FuzzyDictionary",
    "SymSpellIndex",
]


# --------------------------------------------------------------------------
# Problem 1: distance between two strings
# --------------------------------------------------------------------------


def _build_peq(pattern: str) -> Dict[str, int]:
    """Character -> bitmask of the positions where it occurs in ``pattern``."""
    peq: Dict[str, int] = {}
    for i, ch in enumerate(pattern):
        peq[ch] = peq.get(ch, 0) | (1 << i)
    return peq


def levenshtein(a: str, b: str) -> int:
    """Levenshtein edit distance, computed with Myers' bit-vector algorithm.

    The DP column is stored not as `m` integers but as two bitmasks holding its
    **vertical differences**: consecutive cells in a Levenshtein column differ by
    exactly -1, 0 or +1, so two bits per cell suffice. ``vp`` marks the +1
    positions and ``vn`` the -1 positions, and one text character advances the
    whole column through a fixed sequence of and/or/add/shift operations. The
    carry propagation of a single addition does the work that the DP's inner
    ``min`` chain would.

    Args:
        a: First string. Its length sets the bit width.
        b: Second string, scanned one character at a time.

    Returns:
        The minimum number of insertions, deletions and substitutions turning
        ``a`` into ``b``.

    Complexity:
        `O(len(b) * ceil(len(a)/w))` word operations. In CPython the big-integer
        width is unbounded, so this is one pass over ``b`` with `O(m/64)`-word
        arithmetic per step -- roughly 10x faster than the two-row DP at typical
        word lengths, and the gap widens with `m`.

    Example:
        >>> levenshtein("kitten", "sitting")
        3
        >>> levenshtein("", "abc")
        3
    """
    if a == b:
        return 0
    m = len(a)
    if m == 0:
        return len(b)
    if not b:
        return m
    # Bit width follows `a`, so make `a` the shorter string.
    if len(b) < m:
        a, b = b, a
        m = len(a)

    peq = _build_peq(a)
    mask = (1 << m) - 1
    top = 1 << (m - 1)

    vp = mask  # every vertical difference starts at +1 (column 0 is 0,1,2,...)
    vn = 0
    score = m

    for ch in b:
        eq = peq.get(ch, 0)
        xv = eq | vn
        # The single addition below is the heart of the algorithm: its carry
        # chain resolves the whole column's min-propagation at once.
        xh = ((((eq & vp) + vp) & mask) ^ vp) | eq
        ph = vn | (~(xh | vp) & mask)
        mh = vp & xh
        if ph & top:
            score += 1
        elif mh & top:
            score -= 1
        ph = ((ph << 1) | 1) & mask  # the |1 encodes row 0 growing: 0,1,2,...
        mh = (mh << 1) & mask
        vp = (mh | ~(xv | ph)) & mask
        vn = ph & xv

    return score


def levenshtein_dp(
    a: str,
    b: str,
    insert_cost: float = 1.0,
    delete_cost: float = 1.0,
    substitute_cost: float = 1.0,
) -> float:
    """Two-row DP reference implementation, and the escape hatch for custom costs.

    Slower than :func:`levenshtein` and kept for two reasons: the tests use it as
    an independent oracle, and the bit-parallel algorithm **cannot express
    non-unit costs**. Bit-packing works precisely because differences between
    adjacent cells are confined to {-1, 0, +1}; weighted edits break that
    invariant, and there is no known bit-parallel algorithm for the general
    weighted case.

    Costs are directional: the result is the cost of turning ``a`` into ``b``,
    where an *insertion* adds a character of ``b`` and a *deletion* removes a
    character of ``a``. With unequal costs the function is therefore **not
    symmetric**, which is the whole point of having it.

    Args:
        a: The string being transformed.
        b: The target string.
        insert_cost: Cost of inserting a character of ``b``.
        delete_cost: Cost of deleting a character of ``a``.
        substitute_cost: Cost of substituting one character for another.

    Returns:
        The minimum total cost of turning ``a`` into ``b``.

    Complexity:
        `O(len(a) * len(b))` time, `O(min(len(a), len(b)))` space.
    """
    if len(a) > len(b):
        # Keep the inner row short. Reversing the direction of the edit swaps
        # the roles of insertion and deletion, so the costs swap with it.
        a, b = b, a
        insert_cost, delete_cost = delete_cost, insert_cost

    # previous[i] = cost of turning a[:i] into the empty string: i deletions.
    previous = [i * delete_cost for i in range(len(a) + 1)]
    current = [0.0] * (len(a) + 1)
    for j, cb in enumerate(b, start=1):
        # current[0] = cost of turning "" into b[:j]: j insertions.
        current[0] = j * insert_cost
        for i, ca in enumerate(a, start=1):
            current[i] = min(
                current[i - 1] + delete_cost,  # drop a[i-1]
                previous[i] + insert_cost,  # add b[j-1]
                previous[i - 1] + (0.0 if ca == cb else substitute_cost),
            )
        previous, current = current, previous
    return previous[len(a)]


def bounded_levenshtein(a: str, b: str, max_distance: int) -> Optional[int]:
    """Edit distance, or ``None`` if it exceeds ``max_distance``.

    Two cheap tests reject most non-matches before any real work: a length
    difference greater than ``max_distance`` is already a proof, since each edit
    changes the length by at most one. Only survivors reach the bit-parallel
    computation.

    Args:
        a: First string.
        b: Second string.
        max_distance: The threshold.

    Returns:
        The distance if it is at most ``max_distance``, otherwise ``None``.
    """
    if abs(len(a) - len(b)) > max_distance:
        return None
    distance = levenshtein(a, b)
    return distance if distance <= max_distance else None


# --------------------------------------------------------------------------
# Problem 2: approximate substring search
# --------------------------------------------------------------------------


class Match:
    """An approximate occurrence of a pattern in a text."""

    __slots__ = ("end", "distance")

    def __init__(self, end: int, distance: int) -> None:
        #: Index one past the last character of the occurrence.
        self.end = end
        #: Edit distance of the best occurrence ending here.
        self.distance = distance

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Match)
            and self.end == other.end
            and self.distance == other.distance
        )

    def __repr__(self) -> str:
        return f"Match(end={self.end}, distance={self.distance})"


def search(pattern: str, text: str, max_distance: int) -> List[Match]:
    """Find every end position where ``pattern`` occurs within ``max_distance``.

    This is the same bit-parallel machinery as :func:`levenshtein` with **one
    changed boundary condition**. For whole-string distance, row 0 of the DP
    grows `0, 1, 2, ...` because the prefix of the text consumed so far must be
    accounted for. For substring search, a match may begin anywhere, so row 0 is
    all zeros -- which in bit terms means not setting the low bit when shifting
    the horizontal deltas.

    That one bit is the entire difference between "how different are these two
    strings" and "where does this pattern appear". It is worth knowing, because
    it means approximate grep costs exactly as much as one distance computation
    over the whole text, rather than one per starting position.

    Args:
        pattern: The pattern to look for. Must be non-empty.
        text: The text to search.
        max_distance: Maximum edit distance for a reported occurrence.

    Returns:
        Matches in increasing order of end position. Overlapping occurrences are
        all reported; callers wanting one match per region should filter.

    Raises:
        ValueError: If ``pattern`` is empty or ``max_distance`` is negative.

    Complexity:
        `O(len(text) * ceil(len(pattern)/w))`, independent of ``max_distance``.
    """
    if not pattern:
        raise ValueError("pattern must be non-empty")
    if max_distance < 0:
        raise ValueError("max_distance must be non-negative")

    m = len(pattern)
    peq = _build_peq(pattern)
    mask = (1 << m) - 1
    top = 1 << (m - 1)

    vp = mask
    vn = 0
    score = m
    matches: List[Match] = []

    for position, ch in enumerate(text, start=1):
        eq = peq.get(ch, 0)
        xv = eq | vn
        xh = ((((eq & vp) + vp) & mask) ^ vp) | eq
        ph = vn | (~(xh | vp) & mask)
        mh = vp & xh
        if ph & top:
            score += 1
        elif mh & top:
            score -= 1
        # No `| 1` here: row 0 stays zero, so a match may start anywhere.
        ph = (ph << 1) & mask
        mh = (mh << 1) & mask
        vp = (mh | ~(xv | ph)) & mask
        vn = ph & xv
        if score <= max_distance:
            matches.append(Match(end=position, distance=score))

    return matches


# --------------------------------------------------------------------------
# Problem 3: dictionary lookup
# --------------------------------------------------------------------------


class _TrieNode:
    """A trie node. ``word`` is set only on nodes that terminate a term."""

    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: Dict[str, "_TrieNode"] = {}
        self.word: Optional[str] = None


class FuzzyDictionary:
    """Fuzzy dictionary lookup by traversing a trie as a Levenshtein automaton.

    **The idea.** Computing the edit distance from a query to every dictionary
    term recomputes the same DP prefix over and over: `apple`, `apply` and
    `application` share four characters, and so share the first four DP rows. A
    trie stores each distinct prefix once, so a depth-first walk computes each
    shared row **once**, carrying the row down as it descends.

    **Why it is fast.** The row for a trie node gives the edit distance from the
    query to that node's prefix, and edit distance can only grow as the prefix
    grows. So if every entry of a node's row already exceeds the threshold, no
    descendant can ever come back under it -- the whole subtree is pruned
    unvisited. For a threshold of 1 or 2 over a real dictionary this discards
    the overwhelming majority of the trie.

    This is the standard "Levenshtein automaton over a trie" construction
    (Schulz & Mihov 2002). It strictly dominates a BK-tree: same `O(N)` worst
    case, far better pruning in practice, and it shares prefix work that a
    BK-tree -- which indexes by distance to arbitrary pivots -- cannot.

    Example:
        >>> d = FuzzyDictionary(["apple", "apply", "application", "banana"])
        >>> [w for w, _ in d.search("aplpy", 2)]
        ['apply', 'apple']
    """

    def __init__(self, words: Optional[Iterable[str]] = None) -> None:
        """Build a dictionary, optionally pre-loaded with ``words``."""
        self._root = _TrieNode()
        self._size = 0
        if words:
            for word in words:
                self.add(word)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, word: str) -> bool:
        node = self._root
        for ch in word:
            node = node.children.get(ch)  # type: ignore[assignment]
            if node is None:
                return False
        return node.word is not None

    def add(self, word: str) -> None:
        """Insert ``word``. Re-inserting an existing term is a no-op.

        Raises:
            ValueError: If ``word`` is empty.
        """
        if not word:
            raise ValueError("cannot index an empty term")
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
        if node.word is None:
            self._size += 1
        node.word = word

    def search(self, query: str, max_distance: int) -> List[Tuple[str, int]]:
        """Return every term within ``max_distance`` edits of ``query``.

        Args:
            query: The (possibly misspelled) query.
            max_distance: Maximum edit distance.

        Returns:
            ``(word, distance)`` pairs sorted by distance ascending, then
            alphabetically.

        Raises:
            ValueError: If ``max_distance`` is negative.

        Complexity:
            `O(V * len(query))` where `V` is the number of trie nodes surviving
            the prune -- in practice a tiny fraction of the trie.
        """
        if max_distance < 0:
            raise ValueError("max_distance must be non-negative")

        results: List[Tuple[str, int]] = []
        # Row of the DP for the empty prefix: distance from "" to each prefix of
        # the query is just its length.
        first_row = list(range(len(query) + 1))

        if self._root.word is not None and first_row[-1] <= max_distance:
            results.append((self._root.word, first_row[-1]))

        # Explicit stack rather than recursion: dictionary terms can be long
        # enough to matter, and this keeps the traversal independent of
        # Python's recursion limit.
        stack: List[Tuple[_TrieNode, str, List[int]]] = [
            (child, ch, first_row) for ch, child in self._root.children.items()
        ]
        while stack:
            node, ch, parent_row = stack.pop()
            row = self._advance(parent_row, ch, query)
            if node.word is not None and row[-1] <= max_distance:
                results.append((node.word, row[-1]))
            # The prune. Every descendant's row is entrywise >= this one's
            # minimum, so once the minimum exceeds the threshold the entire
            # subtree is unreachable and never gets visited.
            if min(row) <= max_distance:
                for next_ch, child in node.children.items():
                    stack.append((child, next_ch, row))

        results.sort(key=lambda pair: (pair[1], pair[0]))
        return results

    @staticmethod
    def _advance(previous: List[int], ch: str, query: str) -> List[int]:
        """One row of the Levenshtein DP: query against a prefix extended by ``ch``."""
        row = [previous[0] + 1]
        append = row.append
        for j, qc in enumerate(query):
            append(
                min(
                    row[j] + 1,  # insertion
                    previous[j + 1] + 1,  # deletion
                    previous[j] + (0 if qc == ch else 1),  # substitution / match
                )
            )
        return row

    def best_match(
        self, query: str, max_distance: int = 2
    ) -> Optional[Tuple[str, int]]:
        """Return the single closest term, or ``None`` if nothing is close enough."""
        matches = self.search(query, max_distance)
        return matches[0] if matches else None


class SymSpellIndex:
    """Symmetric-delete spelling index (Garbe): near-constant lookup, large index.

    **The idea.** If two words are within `k` edits of each other, then deleting
    at most `k` characters from each can produce a *common* string. So index
    every word under all of its delete-variants, and look a query up by its own
    delete-variants. No edit distance is computed during candidate generation at
    all -- it is pure hash lookup.

    **The trade.** The index holds `sum over words of C(m, <=k)` entries: about
    56 per 10-character word at `k = 2`, and it grows combinatorially in `k`.
    That is why this is the right tool for `k <= 2` -- spelling correction, where
    it is dramatically faster than any tree -- and the wrong one beyond that,
    where :class:`FuzzyDictionary` wins on both memory and time.

    Deletes are generated once per word at build time and once per query at
    lookup time, which is the "symmetric" in the name: the naive version would
    generate insertions, substitutions and transpositions too, at a cost roughly
    the alphabet size times larger.
    """

    def __init__(
        self, words: Optional[Iterable[str]] = None, max_distance: int = 2
    ) -> None:
        """Build an index supporting lookups up to ``max_distance``.

        Args:
            words: Terms to index.
            max_distance: The maximum edit distance the index will support.
                Fixed at construction, because it determines which variants are
                stored.

        Raises:
            ValueError: If ``max_distance`` is negative.
        """
        if max_distance < 0:
            raise ValueError("max_distance must be non-negative")
        self.max_distance = max_distance
        self._index: Dict[str, List[str]] = {}
        self._words: Set[str] = set()
        if words:
            for word in words:
                self.add(word)

    def __len__(self) -> int:
        return len(self._words)

    def __contains__(self, word: str) -> bool:
        return word in self._words

    @property
    def index_entries(self) -> int:
        """Number of distinct delete-variants stored. The price of the speed."""
        return len(self._index)

    def _deletes(self, word: str) -> Set[str]:
        """All strings obtainable by deleting up to ``max_distance`` characters."""
        variants = {word}
        frontier = {word}
        for _ in range(self.max_distance):
            nxt: Set[str] = set()
            for candidate in frontier:
                for i in range(len(candidate)):
                    shorter = candidate[:i] + candidate[i + 1 :]
                    if shorter not in variants:
                        variants.add(shorter)
                        nxt.add(shorter)
            frontier = nxt
            if not frontier:
                break
        return variants

    def add(self, word: str) -> None:
        """Index ``word``.

        Raises:
            ValueError: If ``word`` is empty.
        """
        if not word:
            raise ValueError("cannot index an empty term")
        if word in self._words:
            return
        self._words.add(word)
        for variant in self._deletes(word):
            self._index.setdefault(variant, []).append(word)

    def search(
        self, query: str, max_distance: Optional[int] = None
    ) -> List[Tuple[str, int]]:
        """Return every term within ``max_distance`` edits of ``query``.

        Args:
            query: The query term.
            max_distance: Threshold; defaults to the index's build-time maximum
                and may not exceed it.

        Returns:
            ``(word, distance)`` pairs sorted by distance then alphabetically.

        Raises:
            ValueError: If ``max_distance`` exceeds what the index was built for.
        """
        if max_distance is None:
            max_distance = self.max_distance
        if max_distance > self.max_distance:
            raise ValueError(
                f"index was built for max_distance={self.max_distance}, "
                f"cannot answer {max_distance}"
            )

        candidates: Set[str] = set()
        for variant in self._deletes(query):
            candidates.update(self._index.get(variant, ()))

        # Candidate generation is heuristic and over-generates; every survivor
        # is verified with a real distance computation.
        results = []
        for word in candidates:
            distance = bounded_levenshtein(query, word, max_distance)
            if distance is not None:
                results.append((word, distance))
        results.sort(key=lambda pair: (pair[1], pair[0]))
        return results


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import random
    import string
    import time

    rng = random.Random(4242)
    vocabulary = sorted(
        {
            "".join(
                rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(4, 12))
            )
            for _ in range(50_000)
        }
    )
    queries = [
        "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(4, 12)))
        for _ in range(200)
    ]

    print("--- distance between two strings ---")
    a = "".join(rng.choice("acgt") for _ in range(2000))
    b = "".join(rng.choice("acgt") for _ in range(2000))
    t0 = time.perf_counter()
    fast = levenshtein(a, b)
    t_fast = time.perf_counter() - t0
    t0 = time.perf_counter()
    slow = levenshtein_dp(a, b)
    t_slow = time.perf_counter() - t0
    assert fast == slow
    print(f"  2000 x 2000 characters, distance {fast}")
    print(f"    Myers bit-parallel {t_fast * 1e3:8.2f}ms")
    print(
        f"    two-row DP         {t_slow * 1e3:8.2f}ms   ({t_slow / t_fast:.0f}x slower)"
    )

    print("\n--- dictionary lookup over 50,000 words ---")
    t0 = time.perf_counter()
    fuzzy = FuzzyDictionary(vocabulary)
    t_build_trie = time.perf_counter() - t0
    t0 = time.perf_counter()
    sym = SymSpellIndex(vocabulary, max_distance=3)
    t_build_sym = time.perf_counter() - t0
    print(
        f"  build: trie {t_build_trie:.2f}s, SymSpell {t_build_sym:.2f}s "
        f"({sym.index_entries:,} index entries)"
    )

    def linear(query: str, k: int):
        return sorted(
            (
                (w, d)
                for w in vocabulary
                if (d := bounded_levenshtein(query, w, k)) is not None
            ),
            key=lambda pair: (pair[1], pair[0]),
        )

    print(
        f"\n  {'k':>3}{'linear':>12}{'trie':>12}{'SymSpell':>12}"
        f"{'trie x':>9}{'sym x':>9}"
    )
    for k in (1, 2, 3):
        sample = queries[:40]
        t0 = time.perf_counter()
        expected = [linear(q, k) for q in sample[:10]]
        t_linear = (time.perf_counter() - t0) / 10

        t0 = time.perf_counter()
        trie_results = [fuzzy.search(q, k) for q in sample]
        t_trie = (time.perf_counter() - t0) / len(sample)

        t0 = time.perf_counter()
        sym_results = [sym.search(q, k) for q in sample]
        t_sym = (time.perf_counter() - t0) / len(sample)

        assert trie_results[:10] == expected
        assert sym_results[:10] == expected
        print(
            f"  {k:>3}{t_linear * 1e3:>10.2f}ms{t_trie * 1e3:>10.2f}ms"
            f"{t_sym * 1e3:>10.2f}ms{t_linear / t_trie:>8.1f}x{t_linear / t_sym:>8.0f}x"
        )
    print("\n  Note: the trie automaton's pruning power falls off sharply with k,")
    print("  because every node within k levels of the root must be explored.")

    print("\n--- approximate substring search ---")
    text = "".join(rng.choice("acgt") for _ in range(2_000_000))
    pattern = text[1_234_567 : 1_234_567 + 30]
    t0 = time.perf_counter()
    hits = search(pattern, text, 3)
    print(
        f"  30-char pattern in 2,000,000 characters, distance<=3: "
        f"{len(hits)} end positions in {time.perf_counter() - t0:.2f}s"
    )
