"""Tests for the bit-parallel and automaton-based approximate matching."""

import itertools
import pathlib
import random
import string
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Approximate String Matching"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_matching import (  # noqa: E402
    FuzzyDictionary,
    SymSpellIndex,
    bounded_levenshtein,
    levenshtein,
    levenshtein_dp,
    search,
)

WORDS = ["apple", "apply", "application", "ape", "banana", "band", "bandana", "cherry"]


def reference_search(pattern, text, max_distance):
    """Semi-global DP: end positions of approximate occurrences. Independent oracle."""
    m = len(pattern)
    previous = list(range(m + 1))
    out = []
    for j, tc in enumerate(text, start=1):
        current = [0]
        for i, pc in enumerate(pattern, start=1):
            current.append(
                min(current[i - 1] + 1, previous[i] + 1, previous[i - 1] + (pc != tc))
            )
        if current[m] <= max_distance:
            out.append((j, current[m]))
        previous = current
    return out


def linear_scan(words, query, max_distance):
    """Brute-force dictionary search, used as the oracle for both indexes."""
    hits = []
    for word in words:
        distance = bounded_levenshtein(query, word, max_distance)
        if distance is not None:
            hits.append((word, distance))
    hits.sort(key=lambda pair: (pair[1], pair[0]))
    return hits


# --------------------------------------------------------------------------
# Edit distance
# --------------------------------------------------------------------------


def test_known_distances():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("saturday", "sunday") == 3
    assert levenshtein("flaw", "lawn") == 2
    assert levenshtein("abc", "abc") == 0
    assert levenshtein("", "") == 0
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "") == 3


def test_bit_parallel_matches_the_dp_exhaustively_on_short_strings():
    """Every pair over {a,b} up to length 5, both directions. 4096+ cases."""
    strings = ["".join(t) for n in range(6) for t in itertools.product("ab", repeat=n)]
    for a in strings:
        for b in strings:
            assert levenshtein(a, b) == int(levenshtein_dp(a, b)), (a, b)


def test_bit_parallel_matches_the_dp_on_random_long_strings():
    rng = random.Random(20260831)
    for _ in range(300):
        a = "".join(rng.choice("abcde") for _ in range(rng.randrange(0, 120)))
        b = "".join(rng.choice("abcde") for _ in range(rng.randrange(0, 120)))
        assert levenshtein(a, b) == int(levenshtein_dp(a, b))


def test_distance_is_symmetric_and_a_metric():
    rng = random.Random(5)
    pool = [
        "".join(rng.choice("abc") for _ in range(rng.randrange(0, 12)))
        for _ in range(30)
    ]
    for a, b, c in itertools.islice(itertools.product(pool, repeat=3), 400):
        assert levenshtein(a, b) == levenshtein(b, a)
        assert levenshtein(a, b) <= levenshtein(a, c) + levenshtein(c, b)


def test_patterns_longer_than_a_machine_word_work():
    """Python's big integers remove the 64-character limit the algorithm has in C."""
    a = "abcdefgh" * 40  # 320 characters
    b = a[:150] + "X" + a[151:]
    assert levenshtein(a, b) == 1
    assert levenshtein(a, a[:-5]) == 5


def test_unicode_is_handled():
    assert levenshtein("café", "cafe") == 1
    assert levenshtein("日本語", "日本") == 1
    assert levenshtein("naïve", "naive") == 1


def test_custom_costs_use_the_dp_path():
    # Substitution priced above insert+delete, so the DP should route around it.
    assert levenshtein_dp("a", "b", substitute_cost=5.0) == 2.0
    assert levenshtein_dp("a", "b", substitute_cost=1.0) == 1.0
    # "abc" -> "abcd" needs one insertion, and only the insert price applies.
    assert levenshtein_dp("abc", "abcd", insert_cost=0.5) == 0.5
    assert levenshtein_dp("abc", "abcd", delete_cost=0.5) == 1.0


def test_custom_costs_are_directional():
    """With unequal costs the distance is deliberately asymmetric."""
    assert levenshtein_dp("abc", "abcd", insert_cost=0.25) == 0.25
    assert levenshtein_dp("abcd", "abc", insert_cost=0.25) == 1.0
    assert levenshtein_dp("abcd", "abc", delete_cost=0.25) == 0.25


def test_bounded_distance_rejects_on_length_before_computing():
    assert bounded_levenshtein("a", "aaaaaaaa", 2) is None
    assert bounded_levenshtein("kitten", "sitting", 3) == 3
    assert bounded_levenshtein("kitten", "sitting", 2) is None


# --------------------------------------------------------------------------
# Approximate substring search
# --------------------------------------------------------------------------


def test_exact_occurrences_are_found_at_distance_zero():
    hits = search("cat", "the cat sat on the cat", 0)
    assert [h.end for h in hits] == [7, 22]
    assert all(h.distance == 0 for h in hits)


def test_search_finds_an_occurrence_with_one_substitution():
    hits = search("cat", "the cot sat", 1)
    ends = {h.end for h in hits}
    assert 7 in ends  # "cot"


def test_search_matches_the_reference_dp():
    rng = random.Random(31415)
    for _ in range(400):
        pattern = "".join(rng.choice("abc") for _ in range(rng.randrange(1, 10)))
        text = "".join(rng.choice("abc") for _ in range(rng.randrange(0, 60)))
        k = rng.randrange(0, 4)
        got = [(h.end, h.distance) for h in search(pattern, text, k)]
        assert got == reference_search(pattern, text, k), (pattern, text, k)


def test_search_on_empty_text_returns_nothing():
    assert search("abc", "", 2) == []


def test_search_rejects_bad_arguments():
    with pytest.raises(ValueError):
        search("", "abc", 1)
    with pytest.raises(ValueError):
        search("a", "abc", -1)


# --------------------------------------------------------------------------
# Dictionary lookup
# --------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_dictionary_finds_exact_matches_at_distance_zero(factory):
    index = factory(WORDS)
    assert index.search("apple", 0) == [("apple", 0)]
    assert index.search("nope", 0) == []


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_dictionary_corrects_a_transposition(factory):
    index = factory(WORDS)
    words = [w for w, _ in index.search("aplpy", 2)]
    assert "apply" in words


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_dictionary_results_are_sorted_by_distance(factory):
    index = factory(WORDS)
    distances = [d for _, d in index.search("appl", 2)]
    assert distances == sorted(distances)
    assert distances, "expected at least one match within distance 2"


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_dictionary_membership_and_size(factory):
    index = factory(WORDS)
    assert "apple" in index
    assert "appl" not in index
    assert len(index) == len(WORDS)


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_dictionary_rejects_empty_terms(factory):
    with pytest.raises(ValueError):
        factory([""])


@pytest.mark.parametrize("factory", [FuzzyDictionary, SymSpellIndex])
def test_duplicate_insertion_is_idempotent(factory):
    index = factory(WORDS)
    index.add("apple")
    assert len(index) == len(WORDS)
    assert index.search("apple", 0) == [("apple", 0)]


def test_both_indexes_match_the_linear_scan_on_random_dictionaries():
    rng = random.Random(8675309)
    for _ in range(12):
        vocab = sorted(
            {
                "".join(rng.choice("abcd") for _ in range(rng.randrange(1, 8)))
                for _ in range(120)
            }
        )
        trie = FuzzyDictionary(vocab)
        sym = SymSpellIndex(vocab, max_distance=3)
        for _ in range(12):
            query = "".join(rng.choice("abcd") for _ in range(rng.randrange(1, 8)))
            for k in (0, 1, 2, 3):
                expected = linear_scan(vocab, query, k)
                assert trie.search(query, k) == expected, (query, k)
                assert sym.search(query, k) == expected, (query, k)


def test_fuzzy_dictionary_prunes_rather_than_visiting_everything():
    """A tight threshold over a large dictionary must not degrade to a full scan.

    Measured by node visits rather than wall clock so the assertion is stable.
    """
    rng = random.Random(6)
    vocab = sorted(
        {
            "".join(
                rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(5, 10))
            )
            for _ in range(4_000)
        }
    )
    index = FuzzyDictionary(vocab)

    visited = 0
    original = FuzzyDictionary._advance

    def counting(previous, ch, query):
        nonlocal visited
        visited += 1
        return original(previous, ch, query)

    FuzzyDictionary._advance = staticmethod(counting)
    try:
        result = index.search("abcdefg", 1)
    finally:
        FuzzyDictionary._advance = staticmethod(original)

    assert result == linear_scan(vocab, "abcdefg", 1)
    # A full traversal would touch every trie node; pruning must cut that hard.
    total_nodes = sum(1 for _ in _iter_nodes(index))
    assert visited < total_nodes / 4, f"visited {visited} of {total_nodes} nodes"


def _iter_nodes(index):
    stack = [index._root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.children.values())


def test_symspell_rejects_queries_beyond_its_build_distance():
    index = SymSpellIndex(WORDS, max_distance=1)
    assert index.search("aple", 1) == linear_scan(WORDS, "aple", 1)
    with pytest.raises(ValueError):
        index.search("aple", 2)


def test_symspell_index_size_grows_with_max_distance():
    small = SymSpellIndex(WORDS, max_distance=1)
    large = SymSpellIndex(WORDS, max_distance=3)
    assert large.index_entries > small.index_entries > len(WORDS)


def test_best_match_returns_the_closest_term():
    index = FuzzyDictionary(WORDS)
    # "ape" (delete l) and "apple" (insert p) both sit at distance 1, so the
    # documented lexicographic tie-break decides.
    assert index.best_match("aple") == ("ape", 1)
    assert index.best_match("banan") == ("banana", 1)
    assert index.best_match("zzzzzz", 1) is None


def test_negative_thresholds_are_rejected():
    with pytest.raises(ValueError):
        FuzzyDictionary(WORDS).search("a", -1)
    with pytest.raises(ValueError):
        SymSpellIndex(WORDS, max_distance=-1)
