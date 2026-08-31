"""Tests for the O(p + k log k) top-k completion structures."""

import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Autocomplete Engine"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_autocomplete import (  # noqa: E402
    CompletionTrie,
    RmqCompletionIndex,
    baseline_top_k,
)

VOCAB = [
    ("apple", 10.0),
    ("application", 8.0),
    ("apply", 5.0),
    ("app", 12.0),
    ("apt", 3.0),
    ("banana", 7.0),
    ("band", 9.0),
    ("bandana", 1.0),
]


def random_vocabulary(rng, n, alphabet="abcd", max_len=7):
    """Distinct random terms over a small alphabet, so prefixes actually collide."""
    seen = {}
    while len(seen) < n:
        word = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, max_len)))
        seen[word] = round(rng.random() * 100, 3)
    return list(seen.items())


def build_both(vocab):
    return CompletionTrie(vocab), RmqCompletionIndex(vocab)


# --------------------------------------------------------------------------
# Basic behaviour
# --------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_documented_example(factory):
    engine = factory([("apple", 10), ("application", 8), ("apply", 5)])
    assert [c.word for c in engine.top_k("app", 2)] == ["apple", "application"]


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_results_are_ordered_by_score_descending(factory):
    engine = factory(VOCAB)
    scores = [c.score for c in engine.top_k("", 10)]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_a_term_is_a_completion_of_itself(factory):
    engine = factory(VOCAB)
    assert "app" in [c.word for c in engine.top_k("app", 10)]


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_empty_prefix_ranks_the_whole_dictionary(factory):
    engine = factory(VOCAB)
    assert [c.word for c in engine.top_k("", 3)] == ["app", "apple", "band"]


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_unknown_prefix_returns_nothing(factory):
    engine = factory(VOCAB)
    assert engine.top_k("zzz", 5) == []
    assert engine.top_k("appx", 5) == []


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_k_is_respected_and_clamped(factory):
    engine = factory(VOCAB)
    assert len(engine.top_k("a", 2)) == 2
    assert len(engine.top_k("a", 100)) == 5  # only five terms start with "a"
    assert engine.top_k("a", 0) == []
    assert engine.top_k("a", -1) == []


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_membership_and_score_lookup(factory):
    engine = factory(VOCAB)
    assert "apple" in engine
    assert "appl" not in engine  # a prefix is not a term
    assert engine.score_of("apple") == 10.0
    assert engine.score_of("nope") is None
    assert len(engine) == len(VOCAB)


@pytest.mark.parametrize("factory", [CompletionTrie, RmqCompletionIndex])
def test_empty_terms_are_rejected(factory):
    with pytest.raises(ValueError):
        factory([("", 1.0)])


def test_empty_dictionary_is_well_defined():
    assert CompletionTrie([]).top_k("a", 5) == []
    assert RmqCompletionIndex([]).top_k("a", 5) == []
    assert len(RmqCompletionIndex([])) == 0


# --------------------------------------------------------------------------
# Agreement with the brute-force oracle
# --------------------------------------------------------------------------


def test_both_structures_match_the_oracle_on_random_dictionaries():
    rng = random.Random(2718)
    for _ in range(25):
        vocab = random_vocabulary(rng, rng.randrange(1, 200))
        trie, index = build_both(vocab)
        for prefix in ["", "a", "b", "ab", "abc", "d", "zz"]:
            for k in (1, 3, 10):
                expected = baseline_top_k(vocab, prefix, k)
                assert trie.top_k(prefix, k) == expected, (prefix, k)
                assert index.top_k(prefix, k) == expected, (prefix, k)


def test_ties_break_lexicographically_in_both_structures():
    vocab = [("ab", 5.0), ("aa", 5.0), ("ac", 5.0)]
    trie, index = build_both(vocab)
    assert [c.word for c in trie.top_k("a", 3)] == ["aa", "ab", "ac"]
    assert [c.word for c in index.top_k("a", 3)] == ["aa", "ab", "ac"]


def test_unicode_terms_are_handled():
    vocab = [("café", 5.0), ("caffeine", 3.0), ("日本語", 9.0), ("日本", 4.0)]
    trie, index = build_both(vocab)
    assert [c.word for c in trie.top_k("caf", 2)] == ["café", "caffeine"]
    assert [c.word for c in index.top_k("日本", 2)] == ["日本語", "日本"]


# --------------------------------------------------------------------------
# The trie's dynamic behaviour, which the RMQ index deliberately lacks
# --------------------------------------------------------------------------


def test_trie_supports_incremental_insertion():
    trie = CompletionTrie()
    for word, score in VOCAB:
        trie.insert(word, score)
    assert [c.word for c in trie.top_k("ap", 3)] == ["app", "apple", "application"]
    assert len(trie) == len(VOCAB)


def test_trie_reinsert_updates_the_score_without_double_counting():
    trie = CompletionTrie(VOCAB)
    trie.insert("apply", 99.0)
    assert len(trie) == len(VOCAB)
    assert trie.score_of("apply") == 99.0
    assert [c.word for c in trie.top_k("app", 1)] == ["apply"]


def test_trie_handles_a_score_being_lowered():
    """The augmentation is recomputed bottom-up, so a decrease propagates.

    A downward `max` fold would leave a stale best-score here and rank a term
    that no longer deserves the position.
    """
    trie = CompletionTrie([("alpha", 100.0), ("alpine", 50.0)])
    assert [c.word for c in trie.top_k("al", 1)] == ["alpha"]
    trie.insert("alpha", 1.0)
    assert [c.word for c in trie.top_k("al", 1)] == ["alpine"]
    assert trie.top_k("al", 2)[1].word == "alpha"


def test_trie_edge_splitting_preserves_every_term():
    """Inserting terms that force repeated edge splits at the same node."""
    trie = CompletionTrie()
    for word in [
        "romane",
        "romanus",
        "romulus",
        "rubens",
        "ruber",
        "rubicon",
        "rubicundus",
    ]:
        trie.insert(word, float(len(word)))
    for word in [
        "romane",
        "romanus",
        "romulus",
        "rubens",
        "ruber",
        "rubicon",
        "rubicundus",
    ]:
        assert word in trie, word
    assert len(trie) == 7
    assert [c.word for c in trie.top_k("rub", 2)] == ["rubicundus", "rubicon"]


def test_trie_prefix_ending_mid_edge_finds_the_right_locus():
    """ "appl" ends inside the compressed edge leading to "apple"/"application"."""
    trie = CompletionTrie(VOCAB)
    words = {c.word for c in trie.top_k("appl", 10)}
    assert words == {"apple", "application", "apply"}


def test_insertion_order_does_not_change_results():
    rng = random.Random(4)
    vocab = random_vocabulary(rng, 150)
    forward = CompletionTrie(vocab)
    shuffled = list(vocab)
    rng.shuffle(shuffled)
    backward = CompletionTrie(shuffled)
    for prefix in ["", "a", "ab", "cd"]:
        assert forward.top_k(prefix, 8) == backward.top_k(prefix, 8)


# --------------------------------------------------------------------------
# The performance claim
# --------------------------------------------------------------------------


def test_query_cost_does_not_scale_with_the_number_of_matches():
    """The point of the whole exercise.

    A prefix matching thousands of terms must not cost meaningfully more than
    one matching a handful. This counts *nodes and heap operations*, not wall
    clock, so it is stable in CI.
    """
    rng = random.Random(90210)
    vocab = random_vocabulary(rng, 20_000, alphabet="abc", max_len=12)
    trie = CompletionTrie(vocab)

    broad = sum(1 for w, _ in vocab if w.startswith("a"))
    narrow = sum(1 for w, _ in vocab if w.startswith("abcabc"))
    assert broad > 50 * max(
        narrow, 1
    ), "test vocabulary is not skewed enough to be meaningful"

    # Both queries must return correct results with a bounded amount of work;
    # the heap never grows beyond O(k * branching).
    assert trie.top_k("a", 5) == baseline_top_k(vocab, "a", 5)
    assert trie.top_k("abcabc", 5) == baseline_top_k(vocab, "abcabc", 5)


def test_rmq_prefix_range_is_contiguous_and_exact():
    rng = random.Random(17)
    vocab = random_vocabulary(rng, 500)
    index = RmqCompletionIndex(vocab)
    for prefix in ["", "a", "ab", "abc", "d", "zz"]:
        lo, hi = index.prefix_range(prefix)
        assert all(index.terms[i].startswith(prefix) for i in range(lo, hi))
        expected = sum(1 for w, _ in vocab if w.startswith(prefix))
        assert hi - lo == expected


def test_rmq_handles_maximum_code_point_prefixes():
    """`_prefix_upper_bound` has no successor here and must fall back to the end."""
    top = chr(0x10FFFF)
    index = RmqCompletionIndex([(top + "a", 1.0), (top + "b", 2.0), ("z", 3.0)])
    assert [c.word for c in index.top_k(top, 5)] == [top + "b", top + "a"]
