from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from random import Random
from time import perf_counter
from typing import Callable, Dict, Iterable, List, Sequence, Set, Tuple


def levenshtein_distance(source: str, target: str) -> int:
    """Compute Levenshtein edit distance via iterative dynamic programming.

    This implementation keeps only two rows in memory and runs in
    ``O(len(source) * len(target))`` time.
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
    term: str
    children: Dict[int, "BKTreeNode"] = field(default_factory=dict)


class BKTree:
    """Burkhard–Keller tree for approximate matching using any distance metric."""

    def __init__(self, distance_fn: Callable[[str, str], int] = levenshtein_distance):
        self.distance_fn = distance_fn
        self.root: BKTreeNode | None = None

    def add(self, term: str) -> None:
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
        for term in terms:
            self.add(term)

    def search(self, query: str, max_distance: int) -> List[Tuple[int, str]]:
        if self.root is None:
            return []

        matches: List[Tuple[int, str]] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            distance = self.distance_fn(query, node.term)
            if distance <= max_distance:
                matches.append((distance, node.term))

            lower = distance - max_distance
            upper = distance + max_distance
            for edge_distance, child in node.children.items():
                if lower <= edge_distance <= upper:
                    stack.append(child)
        return sorted(matches, key=lambda x: (x[0], x[1]))


class NGramIndex:
    """N-gram inverted index for pruning candidates in large corpora."""

    def __init__(self, n: int = 3, distance_fn: Callable[[str, str], int] = levenshtein_distance):
        if n < 1:
            raise ValueError("n must be positive")
        self.n = n
        self.distance_fn = distance_fn
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.vocabulary: Set[str] = set()

    def _extract_ngrams(self, term: str) -> Set[str]:
        padded = f"^{term}$"
        return {padded[i : i + self.n] for i in range(len(padded) - self.n + 1)}

    def add(self, term: str) -> None:
        if term in self.vocabulary:
            return
        self.vocabulary.add(term)
        for gram in self._extract_ngrams(term):
            self.inverted_index[gram].add(term)

    def build(self, terms: Iterable[str]) -> None:
        for term in terms:
            self.add(term)

    def candidates(self, query: str, min_shared: int = 1) -> Set[str]:
        query_ngrams = self._extract_ngrams(query)
        counter: Dict[str, int] = defaultdict(int)
        for gram in query_ngrams:
            for term in self.inverted_index.get(gram, ()):  # type: ignore[arg-type]
                counter[term] += 1
        return {term for term, shared in counter.items() if shared >= min_shared}

    def search(self, query: str, max_distance: int, min_shared: int = 1) -> List[Tuple[int, str]]:
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

    Returns timing information for building and querying each structure.
    Benchmarks intentionally keep workloads small to remain test-friendly.
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
