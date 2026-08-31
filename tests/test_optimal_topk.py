"""Tests for the streaming heavy-hitter structures."""

import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Top-K Frequent Items in Stream"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_topk import (  # noqa: E402
    HeavyKeeper,
    MisraGries,
    StreamSummary,
    UnbiasedSpaceSaving,
    evaluate,
    zipf_stream,
)

ALL_STRUCTURES = [
    ("MisraGries", lambda k: MisraGries(k=k)),
    ("StreamSummary", lambda k: StreamSummary(k=k)),
    ("UnbiasedSpaceSaving", lambda k: UnbiasedSpaceSaving(k=k, seed=1)),
    ("HeavyKeeper", lambda k: HeavyKeeper(k=k, width=8 * k, depth=4, seed=1)),
]


# --------------------------------------------------------------------------
# Every structure must find an overwhelming heavy hitter
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_a_dominant_item_is_always_found(name, factory):
    summary = factory(8)
    stream = ["hot"] * 500 + [f"cold-{i}" for i in range(500)]
    summary.update_many(stream)
    assert summary.top_k(1)[0].item == "hot"


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_all_items_retained_when_they_fit(name, factory):
    summary = factory(20)
    stream = [f"item-{i % 5}" for i in range(200)]
    summary.update_many(stream)
    assert {e.item for e in summary.top_k(5)} == {f"item-{i}" for i in range(5)}


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_results_are_sorted_by_decreasing_count(name, factory):
    summary = factory(20)
    summary.update_many(zipf_stream(200, 5_000, 1.2, seed=4))
    counts = [e.count for e in summary.top_k(10)]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_empty_stream_is_well_defined(name, factory):
    summary = factory(10)
    assert summary.top_k(5) == []
    assert summary.estimate("anything").count == 0


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_non_positive_weights_are_rejected(name, factory):
    summary = factory(10)
    with pytest.raises(ValueError):
        summary.update("x", weight=0)
    with pytest.raises(ValueError):
        summary.update("x", weight=-3)


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_weight_matches_repeated_unit_updates(name, factory):
    weighted = factory(10)
    weighted.update("a", weight=5)
    repeated = factory(10)
    for _ in range(5):
        repeated.update("a")
    assert weighted.estimate("a").count == repeated.estimate("a").count


@pytest.mark.parametrize("name,factory", ALL_STRUCTURES)
def test_recall_is_high_on_a_zipfian_stream(name, factory):
    """The workload these structures exist for."""
    stream = zipf_stream(2_000, 50_000, 1.2, seed=7)
    summary = factory(100)
    summary.update_many(stream)
    report = evaluate(name, summary, stream, k=20)
    assert report.recall >= 0.75, f"{name} recall {report.recall}"


# --------------------------------------------------------------------------
# Misra-Gries: the guarantee and the merge
# --------------------------------------------------------------------------


def test_misra_gries_never_overcounts():
    """Its defining one-sided guarantee."""
    stream = zipf_stream(500, 20_000, 1.1, seed=3)
    truth = collections.Counter(stream)
    mg = MisraGries(k=50)
    mg.update_many(stream)
    for item, count in mg.counters.items():
        assert count <= truth[item], f"{item}: reported {count}, actual {truth[item]}"


def test_misra_gries_error_is_within_the_bound():
    """Every estimate undershoots by at most total/k."""
    stream = zipf_stream(500, 20_000, 1.1, seed=5)
    truth = collections.Counter(stream)
    mg = MisraGries(k=50)
    mg.update_many(stream)
    bound = mg.total / mg.k
    for item in truth:
        assert truth[item] - mg.estimate(item).count <= bound


def test_misra_gries_retains_every_true_heavy_hitter():
    """Nothing above N/k may be missing. This is the guarantee, not a heuristic."""
    stream = zipf_stream(1_000, 40_000, 1.3, seed=9)
    truth = collections.Counter(stream)
    mg = MisraGries(k=20)
    mg.update_many(stream)
    threshold = mg.total / mg.k
    for item, count in truth.items():
        if count > threshold:
            assert item in mg.counters, f"{item} occurs {count} > {threshold}, dropped"


def test_misra_gries_merge_matches_a_single_pass():
    stream = zipf_stream(1_000, 40_000, 1.2, seed=11)
    half = len(stream) // 2

    left = MisraGries(k=60)
    left.update_many(stream[:half])
    right = MisraGries(k=60)
    right.update_many(stream[half:])
    merged = left.merge(right)

    direct = MisraGries(k=60)
    direct.update_many(stream)

    assert merged.total == direct.total == len(stream)
    assert len(merged) <= merged.capacity
    top_merged = {e.item for e in merged.top_k(10)}
    top_direct = {e.item for e in direct.top_k(10)}
    assert len(top_merged & top_direct) >= 9

    # The merged summary must still respect the never-overcount guarantee.
    truth = collections.Counter(stream)
    for item, count in merged.counters.items():
        assert count <= truth[item]


def test_misra_gries_merge_rejects_mismatched_k():
    with pytest.raises(ValueError):
        MisraGries(k=10).merge(MisraGries(k=20))


def test_misra_gries_rejects_tiny_k():
    with pytest.raises(ValueError):
        MisraGries(k=1)


# --------------------------------------------------------------------------
# Space-Saving: the guarantee, and the O(1) invariant
# --------------------------------------------------------------------------


def test_space_saving_never_undercounts_retained_items():
    """Its defining one-sided guarantee, the mirror image of Misra-Gries."""
    stream = zipf_stream(500, 20_000, 1.1, seed=13)
    truth = collections.Counter(stream)
    ss = StreamSummary(k=50)
    ss.update_many(stream)
    for item, count in ss.counts.items():
        assert count >= truth[item], f"{item}: reported {count} < actual {truth[item]}"


def test_space_saving_true_count_lies_within_the_error_interval():
    stream = zipf_stream(500, 20_000, 1.1, seed=17)
    truth = collections.Counter(stream)
    ss = StreamSummary(k=50)
    ss.update_many(stream)
    for item in ss.counts:
        estimate = ss.estimate(item)
        assert estimate.lower_bound <= truth[item] <= estimate.count


def test_space_saving_bucket_invariant_holds_throughout():
    """min_count must always be the smallest live bucket, maintained in O(1).

    If the invariant "an emptied minimum bucket is succeeded by the next one
    up" ever failed, min_count would drift and evictions would target the wrong
    counter. Checked after every update on a stream designed to churn.
    """
    ss = StreamSummary(k=8)
    stream = zipf_stream(200, 3_000, 0.8, seed=19)
    for item in stream:
        ss.update(item)
        assert ss.min_count == min(
            ss.buckets
        ), "min_count drifted from the true minimum"
        # Buckets and counts must agree exactly.
        flattened = {i for bucket in ss.buckets.values() for i in bucket}
        assert flattened == set(ss.counts)
        for count, bucket in ss.buckets.items():
            assert bucket, "an empty bucket was left behind"
            for entry in bucket:
                assert ss.counts[entry] == count


def test_space_saving_heavy_hitters_have_no_false_positives():
    """Filtering on the guaranteed lower bound makes the list exact."""
    stream = zipf_stream(500, 20_000, 1.2, seed=23)
    truth = collections.Counter(stream)
    ss = StreamSummary(k=60)
    ss.update_many(stream)
    for estimate in ss.heavy_hitters(threshold=0.01):
        assert truth[estimate.item] > 0.01 * len(stream)


def test_space_saving_rejects_invalid_k():
    with pytest.raises(ValueError):
        StreamSummary(k=0)


# --------------------------------------------------------------------------
# Unbiased Space-Saving
# --------------------------------------------------------------------------


def test_unbiased_variant_keeps_the_same_counter_budget():
    uss = UnbiasedSpaceSaving(k=25, seed=2)
    uss.update_many(zipf_stream(1_000, 20_000, 1.1, seed=29))
    assert len(uss) <= 25
    assert uss.min_count == min(uss.buckets)


def test_unbiased_variant_is_reproducible_for_a_fixed_seed():
    stream = zipf_stream(500, 10_000, 1.1, seed=31)
    a = UnbiasedSpaceSaving(k=30, seed=99)
    a.update_many(stream)
    b = UnbiasedSpaceSaving(k=30, seed=99)
    b.update_many(stream)
    assert a.counts == b.counts


def test_unbiased_variant_total_is_conserved():
    """Counts sum to the stream length: it is a sample, not a lossy sketch."""
    stream = zipf_stream(400, 8_000, 1.1, seed=37)
    uss = UnbiasedSpaceSaving(k=40, seed=3)
    uss.update_many(stream)
    assert uss.total == len(stream)


def test_unbiased_variant_rejects_invalid_k():
    with pytest.raises(ValueError):
        UnbiasedSpaceSaving(k=0)


# --------------------------------------------------------------------------
# HeavyKeeper
# --------------------------------------------------------------------------


def test_heavy_keeper_wins_on_a_heavy_tail_and_loses_on_a_heavy_head():
    """The measured, conditional version of HeavyKeeper's claim.

    Decay protects heavy hitters from tail noise, so it helps most where the
    tail is heaviest relative to the head, and not where the head already
    dominates. Asserting an unconditional win would be wrong -- the first draft
    of this test did, and failed.
    """

    def mean_recall(skew, factory, runs=8):
        total = 0.0
        for seed in range(runs):
            stream = zipf_stream(5_000, 100_000, skew, seed=seed)
            summary = factory(seed)
            summary.update_many(stream)
            total += evaluate("x", summary, stream, 16).recall
        return total / runs

    def heavy_keeper(seed):
        return HeavyKeeper(k=16, width=16, depth=4, seed=seed)

    def space_saving(_seed):
        return StreamSummary(k=64)

    # Light skew, heavy tail: decay pays off.
    assert mean_recall(1.0, heavy_keeper) > mean_recall(1.0, space_saving)
    # Heavy skew, dominant head: exact counting wins instead.
    assert mean_recall(1.3, heavy_keeper) < mean_recall(1.3, space_saving)


def test_heavy_keeper_tracks_at_most_k_items():
    hk = HeavyKeeper(k=10, width=64, depth=4, seed=7)
    hk.update_many(zipf_stream(2_000, 30_000, 1.1, seed=43))
    assert len(hk) <= 10


def test_heavy_keeper_never_overcounts():
    """Decay only ever removes counts, so an estimate cannot exceed the truth."""
    stream = zipf_stream(300, 10_000, 1.2, seed=47)
    truth = collections.Counter(stream)
    hk = HeavyKeeper(k=20, width=128, depth=4, seed=11)
    hk.update_many(stream)
    for estimate in hk.top_k(20):
        assert estimate.count <= truth[estimate.item]


def test_heavy_keeper_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        HeavyKeeper(k=0)
    with pytest.raises(ValueError):
        HeavyKeeper(k=5, depth=0)
    with pytest.raises(ValueError):
        HeavyKeeper(k=5, decay_base=1.0)


# --------------------------------------------------------------------------
# The workload generator and the scorer
# --------------------------------------------------------------------------


def test_zipf_stream_is_skewed_and_reproducible():
    a = zipf_stream(1_000, 20_000, 1.2, seed=53)
    b = zipf_stream(1_000, 20_000, 1.2, seed=53)
    assert a == b
    counts = collections.Counter(a)
    top = [c for _, c in counts.most_common(10)]
    # The most frequent item must dominate the tenth by a wide margin.
    assert top[0] > 5 * top[-1]


def test_evaluate_separates_recall_from_estimation_error():
    stream = zipf_stream(2_000, 40_000, 1.1, seed=59)
    ss = StreamSummary(k=100)
    ss.update_many(stream)
    report = evaluate("ss", ss, stream, k=30)
    assert 0.0 <= report.recall <= 1.0
    assert report.average_relative_error >= 0.0
    # bias includes the misses, so it cannot be better than the retained error.
    assert report.bias <= report.average_relative_error + 1e-9
    assert "ss" in str(report)


def test_evaluate_is_perfect_when_everything_fits():
    stream = [f"item-{i % 5}" for i in range(1_000)]
    ss = StreamSummary(k=20)
    ss.update_many(stream)
    report = evaluate("ss", ss, stream, k=5)
    assert report.recall == 1.0
    assert report.average_relative_error == pytest.approx(0.0)
    assert report.bias == pytest.approx(0.0)
