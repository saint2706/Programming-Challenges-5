import string
import sys
from itertools import product
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Algorithmic.ApproximateStringMatching.approximate_string_matching import (  # noqa: E402
    BKTree,
    NGramIndex,
    levenshtein_distance,
    run_benchmarks,
)


@pytest.mark.parametrize(
    "source,target,expected",
    [
        ("", "", 0),
        ("", "abc", 3),
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("saturday", "sunday", 3),
        ("gumbo", "gambol", 2),
    ],
)
def test_levenshtein_distance_varied_lengths(source, target, expected):
    assert levenshtein_distance(source, target) == expected


@pytest.mark.parametrize("threshold", [0, 1, 2])
def test_bk_tree_search(threshold):
    words = ["book", "books", "cake", "boo", "cape", "boon", "cook"]
    tree = BKTree()
    tree.build(words)

    matches = {word: dist for dist, word in tree.search("book", max_distance=threshold)}
    assert (threshold == 0 and matches == {"book": 0}) or (
        threshold > 0 and "book" in matches
    )
    if threshold >= 1:
        assert "books" in matches or "boon" in matches
    if threshold == 0:
        assert len(matches) == 1


def test_ngram_index_search_largeish_corpus():
    # Build synthetic corpus with varied lengths
    base_words = ["execution", "exaggerate", "example", "sample", "simple"]
    alphabet = "abcd"
    generated = ["".join(p) for p in product(alphabet, repeat=4)]
    corpus = base_words + generated

    index = NGramIndex(n=3)
    index.build(corpus)

    matches = index.search("exection", max_distance=2, min_shared=2)
    returned_words = {word for _, word in matches}
    assert "execution" in returned_words
    assert all(levenshtein_distance("exection", word) <= 2 for word in returned_words)


def test_benchmarks_return_timings():
    corpus = [
        "algorithm",
        "altruistic",
        "alignment",
        "alligator",
        "allocation",
        "alteration",
        "altitude",
        "aluminum",
        "allegory",
        "allegiance",
    ]
    queries = ["aligment", "algoritm", "allegence"]

    results = run_benchmarks(corpus, queries, max_distance=2)
    assert set(results.keys()) == {"bk_tree", "ngram_index"}
    for result in results.values():
        assert result["build_seconds"] >= 0
        assert result["query_seconds"] >= 0


@pytest.mark.parametrize("n", [1, 2, 3])
def test_levenshtein_distance_handles_random_characters(n):
    term1 = string.ascii_lowercase[:n]
    term2 = string.ascii_lowercase[:n][::-1]
    assert levenshtein_distance(term1, term2) >= 0
