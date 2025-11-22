"""Approximate String Matching algorithms and data structures.

This module implements Levenshtein distance calculation and fuzzy string search
utilities including a BK-Tree and an N-gram index for efficient candidate filtering.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from random import Random
from time import perf_counter
from typing import Callable, Dict, Iterable, List, Sequence, Set, Tuple


def levenshtein_distance(source: str, target: str) -> int:
    """Compute Levenshtein edit distance via iterative dynamic programming.

    This implementation keeps only two rows in memory and runs in
    O(len(source) * len(target)) time.

    Args:
        source: The source string.
        target: The target string.

    Returns:
        int: The Levenshtein distance (min number of edits to transform source to target).
    """
    if source == target:
        return 0
    if len(source) == 0:
        return len(target)
    if len(target) == 0:
        return len(source)

    # Ensure source is the shorter string to use minimal memory.
    if len(source) > len(target):
        source, target = target, source

    previous_row = list(range(len(source) + 1))
    for t_char in target:
        current_row = [previous_row[0] + 1]
        for i, s_char in enumerate(source, start=1):
            insert_cost = current_row[i - 1] + 1
            delete_cost = previous_row[i] + 1
            replace_cost = previous_row[i - 1] + (s_char != t_char)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


@dataclass
class BKTreeNode:
    """A node in the Burkhard-Keller Tree."""

    term: str
    children: Dict[int, "BKTreeNode"] = field(default_factory=dict)


class BKTree:
    """Burkhard–Keller tree for approximate matching using any distance metric.

    A BK-Tree is a metric tree specifically designed for discrete metric spaces,
    making it suitable for approximate string matching.
    """

    def __init__(self, distance_fn: Callable[[str, str], int] = levenshtein_distance):
        """Initialize the BK-Tree.

        Args:
            distance_fn: A function that calculates the distance between two strings.
                         Must satisfy metric properties (triangle inequality).
                         Defaults to Levenshtein distance.
        """
        self.distance_fn = distance_fn
        self.root: BKTreeNode | None = None

    def add(self, term: str) -> None:
        """Add a term to the BK-Tree.

        Args:
            term: The string to add to the tree.
        """
        if self.root is None:
            self.root = BKTreeNode(term)
            return

        node = self.root
        while True:
            dist = self.distance_fn(term, node.term)
            if dist == 0:
                return
            if dist not in node.children:
                node.children[dist] = BKTreeNode(term)
                return
            node = node.children[dist]

    def build(self, terms: Iterable[str]) -> None:
        """Build the tree from a collection of terms.

        Args:
            terms: An iterable of strings to add.
        """
        for term in terms:
            self.add(term)

    def search(self, query: str, max_distance: int) -> List[Tuple[int, str]]:
        """Search for terms within a certain distance of the query.

        Args:
            query: The search string.
            max_distance: The maximum allowed distance (inclusive).

        Returns:
            List[Tuple[int, str]]: A sorted list of (distance, term) tuples.
        """
        if self.root is None:
            return []

        matches: List[Tuple[int, str]] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            distance = self.distance_fn(query, node.term)
            if distance <= max_distance:
                matches.append((distance, node.term))

            # Optimization: Only search children where the edge distance is
            # within [distance - max_dist, distance + max_dist].
            # This is based on the Triangle Inequality.
            lower = distance - max_distance
            upper = distance + max_distance
            for edge_distance, child in node.children.items():
                if lower <= edge_distance <= upper:
                    stack.append(child)
        return sorted(matches, key=lambda x: (x[0], x[1]))


class NGramIndex:
    """N-gram inverted index for pruning candidates in large corpora."""

    def __init__(
        self, n: int = 3, distance_fn: Callable[[str, str], int] = levenshtein_distance
    ):
        """Initialize the N-gram index.

        Args:
            n: The size of the n-grams (default: 3 for trigrams).
            distance_fn: The distance function to use for final verification.
                         Defaults to Levenshtein distance.
        """
        if n < 1:
            raise ValueError("n must be positive")
        self.n = n
        self.distance_fn = distance_fn
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.vocabulary: Set[str] = set()

    def _extract_ngrams(self, term: str) -> Set[str]:
        """Extract n-grams from a term with padding.

        Args:
            term: The input string.

        Returns:
            Set[str]: A set of n-gram strings.
        """
        padded = f"^{term}$"
        return {padded[i : i + self.n] for i in range(len(padded) - self.n + 1)}

    def add(self, term: str) -> None:
        """Add a term to the index.

        Args:
            term: The string to add.
        """
        if term in self.vocabulary:
            return
        self.vocabulary.add(term)
        for gram in self._extract_ngrams(term):
            self.inverted_index[gram].add(term)

    def build(self, terms: Iterable[str]) -> None:
        """Build the index from a collection of terms.

        Args:
            terms: An iterable of strings to add.
        """
        for term in terms:
            self.add(term)

    def candidates(self, query: str, min_shared: int = 1) -> Set[str]:
        """Find candidate terms that share at least `min_shared` n-grams.

        Args:
            query: The search query.
            min_shared: Minimum number of shared n-grams required to be a candidate.

        Returns:
            Set[str]: A set of candidate strings.
        """
        query_ngrams = self._extract_ngrams(query)
        counter: Dict[str, int] = defaultdict(int)
        for gram in query_ngrams:
            for term in self.inverted_index.get(gram, ()):  # type: ignore[arg-type]
                counter[term] += 1
        return {term for term, shared in counter.items() if shared >= min_shared}

    def search(
        self, query: str, max_distance: int, min_shared: int = 1
    ) -> List[Tuple[int, str]]:
        """Search for terms close to the query using n-gram filtering.

        Args:
            query: The search string.
            max_distance: The maximum allowed distance (inclusive).
            min_shared: Minimum shared n-grams for candidate pre-filtering.

        Returns:
            List[Tuple[int, str]]: A sorted list of (distance, term) tuples.
        """
        matches: List[Tuple[int, str]] = []
        for candidate in self.candidates(query, min_shared=min_shared):
            dist = self.distance_fn(query, candidate)
            if dist <= max_distance:
                matches.append((dist, candidate))
        return sorted(matches, key=lambda x: (x[0], x[1]))


def run_benchmarks(
    corpus: Sequence[str],
    queries: Sequence[str],
    max_distance: int = 2,
    seed: int = 13,
) -> Dict[str, Dict[str, float]]:
    """Benchmark BK-tree and n-gram index lookup times.

    Args:
        corpus: A sequence of strings to search within.
        queries: A sequence of strings to search for.
        max_distance: The maximum edit distance for matches.
        seed: Random seed for query sampling if queries is empty.

    Returns:
        Dict[str, Dict[str, float]]: Timing results for build and query phases
        for each method.
    """

    rng = Random(seed)
    sampled_queries = list(queries)
    if not sampled_queries:
        sampled_queries = rng.sample(corpus, k=min(5, len(corpus)))

    # BK-tree benchmark
    bk = BKTree()
    start = perf_counter()
    bk.build(corpus)
    bk_build = perf_counter() - start

    start = perf_counter()
    for query in sampled_queries:
        bk.search(query, max_distance=max_distance)
    bk_query = perf_counter() - start

    # N-gram benchmark
    index = NGramIndex()
    start = perf_counter()
    index.build(corpus)
    ngram_build = perf_counter() - start

    start = perf_counter()
    for query in sampled_queries:
        index.search(query, max_distance=max_distance, min_shared=1)
    ngram_query = perf_counter() - start

    return {
        "bk_tree": {"build_seconds": bk_build, "query_seconds": bk_query},
        "ngram_index": {"build_seconds": ngram_build, "query_seconds": ngram_query},
    }


__all__ = [
    "levenshtein_distance",
    "BKTree",
    "NGramIndex",
    "run_benchmarks",
]
