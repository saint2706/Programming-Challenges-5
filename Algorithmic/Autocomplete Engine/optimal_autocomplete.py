"""Optimal top-k completion: answer in `O(p + k log k)`, not `O(p + N log N)`.

A plain trie finds the node for a prefix in `O(p)` and then has to *enumerate
the entire subtree* and sort it to rank the completions. For the prefix "a" over
a million-term dictionary that is 100 000 nodes visited to return 10 results --
the ranking step, not the lookup, is the bottleneck, and it scales with the
corpus rather than with `k`.

The fix is to make the trie a **max-heap as well as a trie**: store in every
node the best completion in its subtree. A best-first traversal from the prefix
locus then emits completions in descending score order and touches `O(k)` nodes,
never looking at the rest of the subtree at all.

Two structures implement that idea, with different trade-offs:

* :class:`CompletionTrie` -- path-compressed trie, one augmented field per node.
  Supports insertion and score updates. `O(p + k log k)` queries.
* :class:`RmqCompletionIndex` -- static: terms sorted lexicographically, so a
  prefix is a contiguous *range* and top-k becomes a classic range-maximum
  problem. `O(log n + k log k)` queries with a much smaller memory footprint,
  but no updates.

Both derive from Hsu & Ottaviano, *Space-efficient data structures for top-k
completion*, WWW 2013. See ``OPTIMAL.md`` for the analysis and for the
alternatives that do not work.
"""

from __future__ import annotations

import bisect
import heapq
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Completion",
    "CompletionTrie",
    "RmqCompletionIndex",
    "baseline_top_k",
]

# A completion's rank key: higher score first, then lexicographic. Negating the
# score lets a plain min-heap and plain tuple comparison do the whole ordering.
RankKey = Tuple[float, str]


def _rank_key(word: str, score: float) -> RankKey:
    """The total order used everywhere: score descending, then word ascending."""
    return (-score, word)


@dataclass(frozen=True)
class Completion:
    """One suggestion."""

    word: str
    score: float


# --------------------------------------------------------------------------
# Completion trie
# --------------------------------------------------------------------------


@dataclass
class _Node:
    """A node of the path-compressed trie.

    Attributes:
        label: The edge label from this node's parent (the compressed run of
            characters). Empty at the root.
        children: First character of a child's label -> child node.
        word: The complete term ending here, if this node is terminal.
        score: That term's score, if terminal.
        best: The rank key of the best completion anywhere in this subtree.
            This is the augmentation that makes best-first search possible: it
            lets the traversal know which branch to descend without looking
            inside it.
    """

    label: str
    children: Dict[str, "_Node"] = field(default_factory=dict)
    word: Optional[str] = None
    score: Optional[float] = None
    best: RankKey = (float("inf"), "")

    def own_key(self) -> Optional[RankKey]:
        """This node's own rank key, if it terminates a term."""
        if self.word is None or self.score is None:
            return None
        return _rank_key(self.word, self.score)

    def recompute_best(self) -> None:
        """Refresh ``best`` from this node's own term and its children's ``best``."""
        candidates = [child.best for child in self.children.values()]
        own = self.own_key()
        if own is not None:
            candidates.append(own)
        self.best = min(candidates) if candidates else (float("inf"), "")


class CompletionTrie:
    """Path-compressed trie augmented with per-node best completion.

    Each node records the rank key of the best term in its subtree. A query
    descends to the prefix locus, then runs a best-first search: a priority
    queue holds "expand this node" and "emit this term" entries, ordered by that
    key. Popping repeatedly yields completions in exactly descending score order
    while touching `O(k)` nodes, regardless of how large the subtree is.

    The invariant that makes this correct is that a node's key is the minimum
    (best) of its own term's key and its children's keys. Replacing a popped
    node with those parts therefore leaves the queue's minimum unchanged when
    that node was the best, which is precisely the greedy property best-first
    search needs.

    Path compression matters more than it looks: without it, a query for a
    ten-character prefix pays ten node visits before reaching the locus, and
    each emitted completion pays one heap operation per character rather than
    per branch point.

    Example:
        >>> engine = CompletionTrie()
        >>> engine.insert("apple", 10)
        >>> engine.insert("application", 8)
        >>> engine.insert("apply", 5)
        >>> [c.word for c in engine.top_k("app", 2)]
        ['apple', 'application']
    """

    def __init__(self, terms: Optional[Iterable[Tuple[str, float]]] = None) -> None:
        """Create an engine, optionally pre-loaded with ``(term, score)`` pairs."""
        self._root = _Node(label="")
        self._size = 0
        if terms:
            for word, score in terms:
                self.insert(word, score)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, word: str) -> bool:
        node = self._descend_exact(word)
        return node is not None and node.word == word

    # -- construction ------------------------------------------------------

    def insert(self, word: str, score: float = 1.0) -> None:
        """Insert or re-score ``word``.

        Args:
            word: The term. Must be non-empty.
            score: Its rank score; higher sorts first.

        Raises:
            ValueError: If ``word`` is empty.
        """
        if not word:
            raise ValueError("cannot insert an empty term")

        node = self._root
        path: List[_Node] = [node]
        rest = word
        target: _Node

        while True:
            first = rest[0]
            child = node.children.get(first)
            if child is None:
                target = _Node(label=rest)
                node.children[first] = target
                path.append(target)
                break

            shared = _common_prefix_length(child.label, rest)
            if shared == len(child.label):
                # The whole edge is consumed; walk through it.
                node = child
                path.append(node)
                rest = rest[shared:]
                if not rest:
                    target = node
                    break
                continue

            # The edge and the new term diverge partway along: split the edge.
            split = _Node(label=child.label[:shared])
            child.label = child.label[shared:]
            split.children[child.label[0]] = child
            node.children[first] = split
            path.append(split)

            remainder = rest[shared:]
            if remainder:
                target = _Node(label=remainder)
                split.children[remainder[0]] = target
                path.append(target)
            else:
                target = split
            break

        if target.word is None:
            self._size += 1
        target.word = word
        target.score = float(score)

        # Recompute the augmentation bottom-up. Doing this rather than folding a
        # `min` downward on the way in is what makes *lowering* a score correct
        # as well as raising one.
        for ancestor in reversed(path):
            ancestor.recompute_best()

    # -- queries -----------------------------------------------------------

    def _descend_exact(self, word: str) -> Optional[_Node]:
        """Find the node whose accumulated path spells exactly ``word``."""
        node = self._root
        rest = word
        while rest:
            child = node.children.get(rest[0])
            if child is None or not rest.startswith(child.label):
                return None
            node = child
            rest = rest[len(child.label) :]
        return node

    def _locus(self, prefix: str) -> Optional[_Node]:
        """The highest node whose subtree is exactly the set of terms with ``prefix``.

        A prefix may end partway along a compressed edge; the locus is then the
        node at the far end of that edge, since every term below it still shares
        the prefix.
        """
        if not prefix:
            return self._root
        node = self._root
        rest = prefix
        while rest:
            child = node.children.get(rest[0])
            if child is None:
                return None
            if len(child.label) >= len(rest):
                # Prefix ends inside this edge.
                return child if child.label.startswith(rest) else None
            if not rest.startswith(child.label):
                return None
            node = child
            rest = rest[len(child.label) :]
        return node

    def top_k(self, prefix: str, k: int = 10) -> List[Completion]:
        """Return the ``k`` highest-scoring terms starting with ``prefix``.

        Args:
            prefix: The prefix to complete. The empty string ranks the whole
                dictionary.
            k: Maximum number of suggestions.

        Returns:
            Completions in descending score order, ties broken lexicographically
            ascending. Fewer than ``k`` if the prefix has fewer completions.

        Complexity:
            `O(p + k * b * log(k * b))` where `p` is the prefix length and `b`
            the branching factor -- crucially independent of how many terms
            share the prefix.
        """
        if k <= 0:
            return []
        locus = self._locus(prefix)
        if locus is None or locus.best[0] == float("inf"):
            return []

        # Heap entries: (rank_key, kind, tiebreak, payload).
        # kind 0 = emit a term, 1 = expand a node. At equal keys emitting wins,
        # which is what we want when a node's best completion is its own term.
        counter = 0
        heap: List[Tuple[RankKey, int, int, object]] = [(locus.best, 1, counter, locus)]
        results: List[Completion] = []

        while heap and len(results) < k:
            key, kind, _, payload = heapq.heappop(heap)
            if kind == 0:
                word, score = payload  # type: ignore[misc]
                results.append(Completion(word, score))
                continue

            node: _Node = payload  # type: ignore[assignment]
            own = node.own_key()
            if own is not None:
                counter += 1
                heapq.heappush(heap, (own, 0, counter, (node.word, node.score)))
            for child in node.children.values():
                counter += 1
                heapq.heappush(heap, (child.best, 1, counter, child))
            del key
        return results

    def score_of(self, word: str) -> Optional[float]:
        """Return ``word``'s score, or ``None`` if it is not in the dictionary."""
        node = self._descend_exact(word)
        if node is None or node.word != word:
            return None
        return node.score


def _common_prefix_length(a: str, b: str) -> int:
    """Length of the longest common prefix of ``a`` and ``b``."""
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


# --------------------------------------------------------------------------
# RMQ completion index
# --------------------------------------------------------------------------


def _prefix_upper_bound(prefix: str) -> Optional[str]:
    """Smallest string that sorts after every string beginning with ``prefix``.

    Returns ``None`` when no such string exists (the prefix consists entirely of
    the maximum code point), in which case the range runs to the end of the
    dictionary.
    """
    chars = list(prefix)
    while chars:
        code = ord(chars[-1])
        if code < 0x10FFFF:
            chars[-1] = chr(code + 1)
            return "".join(chars)
        chars.pop()
    return None


class RmqCompletionIndex:
    """Static top-k completion via range-maximum queries.

    Sorting the terms lexicographically turns "all terms with prefix `p`" into a
    **contiguous range** -- found by two binary searches -- and turns top-k
    completion into the well-studied problem of reporting the `k` largest values
    in an array range.

    That problem has a clean recursive solution. Find the maximum in the range;
    it is the first result. It splits the range in two, and the second result is
    the better of those two halves' maxima. Keeping the candidate subranges in a
    priority queue yields results in order, one range-maximum query per result.

    Compared with :class:`CompletionTrie` this gives up insertion entirely, and
    in exchange stores no per-character nodes at all: two flat arrays and a
    segment tree of `2n` integers. For a static dictionary -- a shipped word
    list, a search index rebuilt nightly -- it is the smaller and simpler
    structure.

    Example:
        >>> index = RmqCompletionIndex([("apple", 10), ("application", 8), ("apply", 5)])
        >>> [c.word for c in index.top_k("app", 2)]
        ['apple', 'application']
    """

    def __init__(self, terms: Iterable[Tuple[str, float]]) -> None:
        """Build the index from ``(term, score)`` pairs.

        Later pairs win if a term repeats.

        Args:
            terms: The dictionary.
        """
        deduped: Dict[str, float] = {}
        for word, score in terms:
            if not word:
                raise ValueError("cannot index an empty term")
            deduped[word] = float(score)

        self.terms: List[str] = sorted(deduped)
        self.scores: List[float] = [deduped[w] for w in self.terms]
        self._tree = self._build_tree(self.scores)

    def __len__(self) -> int:
        return len(self.terms)

    def __contains__(self, word: str) -> bool:
        i = bisect.bisect_left(self.terms, word)
        return i < len(self.terms) and self.terms[i] == word

    @staticmethod
    def _build_tree(scores: Sequence[float]) -> List[int]:
        """Iterative max-segment-tree storing *indices*, so ties resolve leftward.

        A sparse table would answer in `O(1)` instead of `O(log n)`, but costs
        `O(n log n)` memory. The heap operations already cost `log k` per result,
        so the segment tree's extra `log n` is rarely the bottleneck, and `2n`
        integers is a much better default. See ``OPTIMAL.md``.
        """
        n = len(scores)
        if n == 0:
            return []
        tree = [0] * (2 * n)
        for i in range(n):
            tree[n + i] = i
        for i in range(n - 1, 0, -1):
            left, right = tree[2 * i], tree[2 * i + 1]
            # Strict `>` keeps the leftmost index on ties, which makes ties
            # break lexicographically because `terms` is sorted.
            tree[i] = left if scores[left] >= scores[right] else right
        return tree

    def _argmax(self, lo: int, hi: int) -> int:
        """Index of the maximum score in ``[lo, hi)``. Leftmost on ties."""
        n = len(self.scores)
        scores = self.scores
        tree = self._tree
        best = -1
        left, right = lo + n, hi + n
        while left < right:
            if left & 1:
                cand = tree[left]
                if best < 0 or scores[cand] > scores[best]:
                    best = cand
                left += 1
            if right & 1:
                right -= 1
                cand = tree[right]
                if best < 0 or scores[cand] > scores[best]:
                    best = cand
            left >>= 1
            right >>= 1
        return best

    def prefix_range(self, prefix: str) -> Tuple[int, int]:
        """Half-open index range of terms starting with ``prefix``."""
        lo = bisect.bisect_left(self.terms, prefix)
        upper = _prefix_upper_bound(prefix)
        hi = len(self.terms) if upper is None else bisect.bisect_left(self.terms, upper)
        return lo, hi

    def top_k(self, prefix: str, k: int = 10) -> List[Completion]:
        """Return the ``k`` highest-scoring terms starting with ``prefix``.

        Args:
            prefix: The prefix to complete.
            k: Maximum number of suggestions.

        Returns:
            Completions in descending score order, ties broken lexicographically.

        Complexity:
            `O(log n + k log k log n)`; independent of the number of terms
            sharing the prefix.
        """
        if k <= 0:
            return []
        lo, hi = self.prefix_range(prefix)
        if lo >= hi:
            return []

        # Heap of candidate subranges keyed by their maximum. Popping a range
        # yields the next result and splits the range around it.
        first = self._argmax(lo, hi)
        heap: List[Tuple[RankKey, int, int, int]] = [
            (_rank_key(self.terms[first], self.scores[first]), first, lo, hi)
        ]
        results: List[Completion] = []

        while heap and len(results) < k:
            _, mid, left, right = heapq.heappop(heap)
            results.append(Completion(self.terms[mid], self.scores[mid]))
            for sub_lo, sub_hi in ((left, mid), (mid + 1, right)):
                if sub_lo < sub_hi:
                    idx = self._argmax(sub_lo, sub_hi)
                    heapq.heappush(
                        heap,
                        (
                            _rank_key(self.terms[idx], self.scores[idx]),
                            idx,
                            sub_lo,
                            sub_hi,
                        ),
                    )
        return results

    def score_of(self, word: str) -> Optional[float]:
        """Return ``word``'s score, or ``None`` if it is not indexed."""
        i = bisect.bisect_left(self.terms, word)
        if i < len(self.terms) and self.terms[i] == word:
            return self.scores[i]
        return None


# --------------------------------------------------------------------------
# Baseline, for tests and benchmarks
# --------------------------------------------------------------------------


def baseline_top_k(
    terms: Sequence[Tuple[str, float]], prefix: str, k: int = 10
) -> List[Completion]:
    """Reference implementation: filter, sort, truncate.

    `O(N log N)` in the size of the whole dictionary. This is what a plain trie
    degenerates to once the ranking step is counted, and it is the thing the two
    structures above exist to beat. Used by the tests as an independent oracle.
    """
    matches = [(w, s) for w, s in terms if w.startswith(prefix)]
    matches.sort(key=lambda ws: _rank_key(ws[0], ws[1]))
    return [Completion(w, s) for w, s in matches[:k]]


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import random
    import string
    import time

    rng = random.Random(20240)
    vocabulary = []
    seen = set()
    while len(vocabulary) < 200_000:
        length = rng.randrange(3, 12)
        word = "".join(rng.choice(string.ascii_lowercase[:8]) for _ in range(length))
        if word not in seen:
            seen.add(word)
            vocabulary.append((word, rng.random() * 1000))

    t0 = time.perf_counter()
    trie = CompletionTrie(vocabulary)
    build_trie = time.perf_counter() - t0

    t0 = time.perf_counter()
    index = RmqCompletionIndex(vocabulary)
    build_index = time.perf_counter() - t0

    print(f"{len(vocabulary)} terms")
    print(f"  CompletionTrie      build {build_trie:6.2f}s")
    print(f"  RmqCompletionIndex  build {build_index:6.2f}s\n")

    queries = ["a", "ab", "abc", "abcd"]
    print(
        f"{'prefix':<8}{'matches':>9}{'baseline':>11}{'trie':>11}{'rmq':>11}{'speedup':>10}"
    )
    for prefix in queries:
        matches = sum(1 for w, _ in vocabulary if w.startswith(prefix))
        reps = 20

        t0 = time.perf_counter()
        for _ in range(reps):
            expected = baseline_top_k(vocabulary, prefix, 10)
        t_base = (time.perf_counter() - t0) / reps

        t0 = time.perf_counter()
        for _ in range(reps):
            got_trie = trie.top_k(prefix, 10)
        t_trie = (time.perf_counter() - t0) / reps

        t0 = time.perf_counter()
        for _ in range(reps):
            got_rmq = index.top_k(prefix, 10)
        t_rmq = (time.perf_counter() - t0) / reps

        assert [c.word for c in got_trie] == [c.word for c in expected]
        assert [c.word for c in got_rmq] == [c.word for c in expected]
        print(
            f"{prefix:<8}{matches:>9}{t_base * 1e3:>10.2f}ms"
            f"{t_trie * 1e3:>10.3f}ms{t_rmq * 1e3:>10.3f}ms{t_base / t_trie:>9.0f}x"
        )
