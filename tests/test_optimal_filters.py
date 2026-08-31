"""Tests for the space-optimal AMQ filters in Algorithmic/Approximate Set Membership."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Approximate Set Membership"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_filters import (  # noqa: E402
    BinaryFuse8Filter,
    BlockedBloomFilter,
    CuckooFilter,
    FuseConstructionError,
    HomogeneousRibbonFilter,
    hash_bytes,
    lower_bound_bits_per_key,
    measure,
    mulhi,
    splitmix64,
)

SMALL = 2_000
PROBES = 20_000


def members(n: int) -> list:
    """Deterministic, well-spread distinct 64-bit keys."""
    return [splitmix64(i) for i in range(n)]


def non_members(n: int) -> list:
    """Keys disjoint from :func:`members` for any reasonable size."""
    return [splitmix64(i) for i in range(1 << 40, (1 << 40) + n)]


# --------------------------------------------------------------------------
# Hashing primitives
# --------------------------------------------------------------------------


def test_splitmix64_avalanches_and_stays_in_range():
    values = {splitmix64(i) for i in range(1000)}
    assert len(values) == 1000
    assert all(0 <= v < 1 << 64 for v in values)


def test_hash_bytes_is_stable_and_length_sensitive():
    assert hash_bytes(b"apple") == hash_bytes(b"apple")
    assert hash_bytes(b"apple") != hash_bytes(b"apples")
    # A trailing NUL must not alias with the shorter string.
    assert hash_bytes(b"apple") != hash_bytes(b"apple\0")


def test_mulhi_matches_the_widening_product():
    assert mulhi(2**64 - 1, 2) == 1
    assert mulhi(2**63, 4) == 2
    assert mulhi(12345, 0) == 0


def test_lower_bound_matches_the_closed_form():
    assert lower_bound_bits_per_key(1 / 256) == pytest.approx(8.0)
    assert lower_bound_bits_per_key(0.01) == pytest.approx(6.6438, abs=1e-3)
    with pytest.raises(ValueError):
        lower_bound_bits_per_key(0.0)


# --------------------------------------------------------------------------
# The one guarantee every AMQ filter must keep: no false negatives
# --------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 17, 500, SMALL])
def test_binary_fuse_has_no_false_negatives(n):
    keys = members(n)
    filt = BinaryFuse8Filter(keys)
    assert all(filt.contains(k) for k in keys)
    assert len(filt) == n


@pytest.mark.parametrize("n", [1, 2, 17, 500, SMALL])
def test_ribbon_has_no_false_negatives(n):
    keys = members(n)
    filt = HomogeneousRibbonFilter(keys, slack=0.05)
    assert all(filt.contains(k) for k in keys)
    assert len(filt) == n


@pytest.mark.parametrize("n", [1, 17, 500, SMALL])
def test_blocked_bloom_has_no_false_negatives(n):
    keys = members(n)
    filt = BlockedBloomFilter(capacity=n, false_positive_rate=1 / 256)
    for k in keys:
        filt.add(k)
    assert all(filt.contains(k) for k in keys)


def test_cuckoo_has_no_false_negatives_below_capacity():
    keys = members(SMALL)
    filt = CuckooFilter(capacity=SMALL, fingerprint_bits=12)
    assert all(filt.add(k) for k in keys)
    assert all(filt.contains(k) for k in keys)


def test_filters_accept_strings_and_bytes_not_just_ints():
    words = ["apple", "banana", "cherry", "durian"]
    for filt in (BinaryFuse8Filter(words), HomogeneousRibbonFilter(words, slack=0.5)):
        assert all(filt.contains(w) for w in words)
    blocked = BlockedBloomFilter(capacity=16)
    for w in words:
        blocked.add(w)
    assert all(blocked.contains(w) for w in words)


# --------------------------------------------------------------------------
# Accuracy
# --------------------------------------------------------------------------


def test_binary_fuse_false_positive_rate_is_near_two_to_the_minus_eight():
    filt = BinaryFuse8Filter(members(20_000))
    hits = sum(1 for k in non_members(PROBES) if filt.contains(k))
    assert hits / PROBES < 0.010  # nominal 0.0039, generous sampling slack


def test_ribbon_false_positive_rate_is_near_two_to_the_minus_eight():
    filt = HomogeneousRibbonFilter(members(20_000), slack=0.05)
    hits = sum(1 for k in non_members(PROBES) if filt.contains(k))
    assert hits / PROBES < 0.010


def test_ribbon_error_collapses_once_slack_times_width_clears_the_cliff():
    """The central empirical finding documented in OPTIMAL.md.

    At slack * w = 1.3 the filter is badly broken; at slack * w = 5.1 it hits
    its nominal rate, at essentially identical memory. Widening the ribbon is
    almost free; adding slots is not.
    """
    keys = members(20_000)
    probes = non_members(PROBES)

    narrow = HomogeneousRibbonFilter(keys, slack=0.02, width=64)
    wide = HomogeneousRibbonFilter(keys, slack=0.02, width=256)

    narrow_fpp = sum(1 for k in probes if narrow.contains(k)) / PROBES
    wide_fpp = sum(1 for k in probes if wide.contains(k)) / PROBES

    assert narrow_fpp > 0.05, "expected the narrow ribbon to be far off nominal"
    assert wide_fpp < 0.010, "expected the wide ribbon to reach nominal"
    # ...and the memory difference is under 1%.
    assert wide.bits_per_key() / narrow.bits_per_key() < 1.01


def test_blocked_bloom_meets_its_target_error_rate():
    n = 20_000
    filt = BlockedBloomFilter(capacity=n, false_positive_rate=1 / 256)
    for k in members(n):
        filt.add(k)
    hits = sum(1 for k in non_members(PROBES) if filt.contains(k))
    assert hits / PROBES < 1 / 256


# --------------------------------------------------------------------------
# Space: the point of the exercise
# --------------------------------------------------------------------------


def test_ribbon_beats_fuse_beats_bloom_on_space():
    n = 20_000
    keys = members(n)
    ribbon = HomogeneousRibbonFilter(keys, slack=0.02)
    fuse = BinaryFuse8Filter(keys)
    blocked = BlockedBloomFilter(capacity=n, false_positive_rate=1 / 256)
    for k in keys:
        blocked.add(k)

    assert ribbon.bits_per_key() < fuse.bits_per_key() < blocked.bits_per_key()
    # The headline claim: within 5% of the information-theoretic lower bound.
    assert ribbon.bits_per_key() < 8.0 * 1.05
    # Classic Bloom sits at 1.44x; the fuse filter must comfortably beat that.
    assert fuse.bits_per_key() < 8.0 * 1.30


def test_measure_reports_space_overhead_against_the_bound():
    keys = members(5_000)
    filt = HomogeneousRibbonFilter(keys, slack=0.02)
    report = measure("ribbon", filt, keys, non_members(PROBES))
    assert report.false_negatives == 0
    assert report.keys == 5_000
    assert 0.9 < report.space_overhead < 1.3
    assert "ribbon" in str(report)


# --------------------------------------------------------------------------
# Failure modes, stated rather than hidden
# --------------------------------------------------------------------------


def test_binary_fuse_rejects_duplicate_keys_instead_of_looping_forever():
    with pytest.raises(FuseConstructionError):
        BinaryFuse8Filter([7] * 64)


def test_ribbon_tolerates_duplicate_keys():
    """A repeated key is a redundant equation; elimination drops it."""
    keys = [7] * 64 + members(100)
    filt = HomogeneousRibbonFilter(keys, slack=0.1)
    assert filt.contains(7)
    assert all(filt.contains(k) for k in members(100))


def test_empty_filters_are_well_defined():
    assert not BinaryFuse8Filter([]).contains(42)
    assert not HomogeneousRibbonFilter([]).contains(42)
    assert BinaryFuse8Filter([]).bits_per_key() == 0.0


def test_cuckoo_supports_deletion_which_the_static_filters_cannot():
    filt = CuckooFilter(capacity=1000, fingerprint_bits=12)
    keys = members(500)
    for k in keys:
        filt.add(k)
    assert filt.contains(keys[0])
    assert filt.remove(keys[0])
    assert len(filt) == 499
    # Removing again should fail: only one fingerprint was stored.
    assert not filt.remove(keys[0])


def test_cuckoo_reports_saturation_rather_than_corrupting_itself():
    filt = CuckooFilter(capacity=64, fingerprint_bits=8)
    inserted = 0
    for k in members(10_000):
        if not filt.add(k):
            break
        inserted += 1
    assert inserted < 10_000, "expected the table to saturate"
    # Everything accepted before saturation must still be found.
    assert all(filt.contains(k) for k in members(inserted))


def test_invalid_parameters_are_rejected():
    with pytest.raises(ValueError):
        BlockedBloomFilter(capacity=10, false_positive_rate=0)
    with pytest.raises(ValueError):
        BlockedBloomFilter(capacity=-1)
    with pytest.raises(ValueError):
        CuckooFilter(capacity=10, fingerprint_bits=2)
    with pytest.raises(ValueError):
        HomogeneousRibbonFilter([1, 2, 3], width=100)
