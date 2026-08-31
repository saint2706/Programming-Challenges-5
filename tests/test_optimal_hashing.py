"""Tests for the consistent hashing algorithms."""

import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "Algorithmic" / "Consistent Hashing Library"
if str(CHALLENGE) not in sys.path:
    sys.path.insert(0, str(CHALLENGE))

import pytest  # noqa: E402
from optimal_hashing import (  # noqa: E402
    AnchorHash,
    HashRing,
    JumpHash,
    MaglevHash,
    RendezvousHash,
    balance,
    compare,
    disruption,
)

KEYS = [f"key-{i}" for i in range(6_000)]
# Load balance is a statistical property: with only a few hundred keys per
# node, sampling noise alone produces a peak/mean around 1.10. Balance
# assertions therefore use a much larger key set than correctness ones.
BALANCE_KEYS = [f"key-{i}" for i in range(60_000)]
NODES = [f"node-{i}" for i in range(12)]


def named_structures():
    """Every algorithm that routes to *named* nodes and supports arbitrary removal."""
    return [
        ("HashRing", lambda names: HashRing(names, virtual_nodes=100)),
        ("RendezvousHash", RendezvousHash),
        ("MaglevHash", lambda names: MaglevHash(names, table_size=4099)),
    ]


# --------------------------------------------------------------------------
# Every algorithm must be a deterministic total function
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name,factory", named_structures())
def test_lookup_is_deterministic_and_in_range(name, factory):
    index = factory(NODES)
    first = [index.lookup(k) for k in KEYS[:500]]
    second = [index.lookup(k) for k in KEYS[:500]]
    assert first == second
    assert set(first) <= set(NODES)


@pytest.mark.parametrize("name,factory", named_structures())
def test_empty_structures_return_none(name, factory):
    assert factory([]).lookup("anything") is None


def test_jump_hash_is_deterministic_and_in_range():
    index = JumpHash(17)
    assert all(0 <= index.lookup(k) < 17 for k in KEYS[:500])
    assert [index.lookup(k) for k in KEYS[:100]] == [
        index.lookup(k) for k in KEYS[:100]
    ]


def test_anchor_hash_is_deterministic_and_returns_working_buckets():
    anchor = AnchorHash(capacity=32, working=12)
    working = set(anchor.working_set)
    assert all(anchor.lookup(k) in working for k in KEYS[:500])


# --------------------------------------------------------------------------
# Balance
# --------------------------------------------------------------------------


def test_all_algorithms_balance_within_a_reasonable_factor():
    cheap = [
        ("HashRing", HashRing(NODES, virtual_nodes=100)),
        ("MaglevHash", MaglevHash(NODES, table_size=4099)),
        ("JumpHash", JumpHash(12)),
        ("AnchorHash", AnchorHash(capacity=24, working=12)),
    ]
    for name, index in cheap:
        ratio = balance([index.lookup(k) for k in BALANCE_KEYS])
        assert ratio < 1.20, f"{name} peak/mean {ratio}"

    # Rendezvous is O(N) per lookup, so it gets the smaller sample and a bound
    # loose enough to absorb the resulting sampling noise.
    rendezvous = RendezvousHash(NODES)
    assert balance([rendezvous.lookup(k) for k in KEYS]) < 1.25


def test_ring_is_the_worst_balanced_of_the_five():
    """The ring's defining weakness, measured on a sample large enough to see it.

    Even at 100 virtual nodes per server the ring's peak/mean is several times
    further from 1.0 than any of its successors.
    """
    ring_index = HashRing(NODES, virtual_nodes=100)
    anchor_index = AnchorHash(capacity=24, working=12)
    jump_index = JumpHash(12)
    ring = balance([ring_index.lookup(k) for k in BALANCE_KEYS])
    anchor = balance([anchor_index.lookup(k) for k in BALANCE_KEYS])
    jump = balance([jump_index.lookup(k) for k in BALANCE_KEYS])
    assert ring > anchor
    assert ring > jump
    assert ring - 1.0 > 2 * (anchor - 1.0), f"ring {ring}, anchor {anchor}"


def test_ring_balance_improves_with_more_virtual_nodes():
    """The trade the ring is stuck with: balance costs memory linearly."""
    coarse_ring = HashRing(NODES, virtual_nodes=1)
    fine_ring = HashRing(NODES, virtual_nodes=400)
    coarse = balance([coarse_ring.lookup(k) for k in KEYS])
    fine = balance([fine_ring.lookup(k) for k in KEYS])
    assert coarse > fine
    assert coarse > 1.5, "one point per node should be badly unbalanced"


def test_jump_hash_covers_every_bucket_roughly_evenly():
    index = JumpHash(8)
    counts = collections.Counter(index.lookup(k) for k in KEYS)
    assert set(counts) == set(range(8))
    assert max(counts.values()) / min(counts.values()) < 1.25


# --------------------------------------------------------------------------
# Minimal disruption -- the property that matters
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,factory",
    [
        ("HashRing", lambda names: HashRing(names, virtual_nodes=100)),
        ("RendezvousHash", RendezvousHash),
    ],
)
def test_removal_moves_only_the_departing_nodes_keys(name, factory):
    victim = NODES[5]
    before_index = factory(NODES)
    after_index = factory([n for n in NODES if n != victim])
    before = [before_index.lookup(k) for k in KEYS]
    after = [after_index.lookup(k) for k in KEYS]
    needless = [(a, b) for a, b in zip(before, after) if a != b and a != victim]
    assert needless == [], f"{name} moved {len(needless)} keys it did not need to"


def test_anchor_hash_removal_is_minimally_disruptive():
    anchor = AnchorHash(capacity=24, working=12)
    before = [anchor.lookup(k) for k in KEYS]
    anchor.remove(5)
    after = [anchor.lookup(k) for k in KEYS]
    needless = [(a, b) for a, b in zip(before, after) if a != b and a != 5]
    assert needless == []
    assert 5 not in set(after)


def test_jump_hash_tail_removal_is_minimally_disruptive():
    big, small = JumpHash(12), JumpHash(11)
    before = [big.lookup(k) for k in KEYS]
    after = [small.lookup(k) for k in KEYS]
    needless = [(a, b) for a, b in zip(before, after) if a != b and a != 11]
    assert needless == []


def test_maglev_is_not_minimally_disruptive():
    """Documented, deliberate, and the reason Maglev is not the default answer."""
    victim = NODES[5]
    before_index = MaglevHash(NODES, table_size=4099)
    after_index = MaglevHash([n for n in NODES if n != victim], table_size=4099)
    before = [before_index.lookup(k) for k in KEYS]
    after = [after_index.lookup(k) for k in KEYS]
    needless = sum(1 for a, b in zip(before, after) if a != b and a != victim)
    assert needless > 0, "expected Maglev to reshuffle keys of surviving nodes"


def test_anchor_hash_add_restores_the_previous_assignment():
    """Remove then re-add must return every key to where it started."""
    anchor = AnchorHash(capacity=24, working=12)
    before = [anchor.lookup(k) for k in KEYS[:3_000]]
    anchor.remove(7)
    anchor.add()
    after = [anchor.lookup(k) for k in KEYS[:3_000]]
    assert before == after


def test_anchor_hash_survives_many_removals_and_additions():
    anchor = AnchorHash(capacity=32, working=16)
    for bucket in (3, 11, 0, 15, 8):
        anchor.remove(bucket)
    assert anchor.size == 11
    working = set(anchor.working_set)
    assert working.isdisjoint({3, 11, 0, 15, 8})
    assert all(anchor.lookup(k) in working for k in KEYS[:2_000])

    for _ in range(5):
        anchor.add()
    assert anchor.size == 16
    assert set(anchor.working_set) == set(range(16))


# --------------------------------------------------------------------------
# Weighting, which only rendezvous does natively
# --------------------------------------------------------------------------


def test_rendezvous_weights_shift_load_proportionally():
    index = RendezvousHash({"small": 1.0, "large": 4.0})
    counts = collections.Counter(index.lookup(k) for k in KEYS)
    share = counts["large"] / len(KEYS)
    # Weight 4 against weight 1 means an expected 80% share.
    assert 0.76 < share < 0.84, f"large node took {share:.3f}"


def test_rendezvous_rank_gives_a_stable_replica_set():
    index = RendezvousHash(NODES)
    replicas = index.rank("some-key", 3)
    assert len(replicas) == 3
    assert len(set(replicas)) == 3
    assert replicas[0] == index.lookup("some-key")
    # Removing a node outside the replica set must not perturb it.
    index.remove(next(n for n in NODES if n not in replicas))
    assert index.rank("some-key", 3) == replicas


def test_rendezvous_rejects_non_positive_weights():
    with pytest.raises(ValueError):
        RendezvousHash({"a": 0.0})
    with pytest.raises(ValueError):
        RendezvousHash({"a": -1.0})


# --------------------------------------------------------------------------
# Argument validation
# --------------------------------------------------------------------------


def test_invalid_arguments_are_rejected():
    with pytest.raises(ValueError):
        HashRing(NODES, virtual_nodes=0)
    with pytest.raises(ValueError):
        JumpHash(0)
    with pytest.raises(ValueError):
        MaglevHash(NODES, table_size=100)  # not prime
    with pytest.raises(ValueError):
        AnchorHash(capacity=0)
    with pytest.raises(ValueError):
        AnchorHash(capacity=4, working=5)


def test_anchor_hash_rejects_invalid_removals():
    anchor = AnchorHash(capacity=8, working=3)
    anchor.remove(1)
    with pytest.raises(ValueError):
        anchor.remove(1)  # already gone
    with pytest.raises(ValueError):
        anchor.remove(99)  # out of range
    anchor.remove(0)
    with pytest.raises(ValueError):
        anchor.remove(2)  # would empty the working set


def test_anchor_hash_rejects_adding_beyond_capacity():
    anchor = AnchorHash(capacity=4, working=4)
    with pytest.raises(ValueError):
        anchor.add()


def test_removing_an_absent_node_is_a_noop():
    ring = HashRing(NODES)
    ring.remove("not-a-node")
    assert ring.nodes == NODES
    index = RendezvousHash(NODES)
    index.remove("not-a-node")
    assert sorted(index.nodes) == sorted(NODES)


# --------------------------------------------------------------------------
# Measurement helpers
# --------------------------------------------------------------------------


def test_balance_and_disruption_helpers():
    assert balance(["a", "a", "b", "b"]) == pytest.approx(1.0)
    assert balance(["a", "a", "a", "b"]) == pytest.approx(1.5)
    assert disruption(["a", "b"], ["a", "b"]) == 0.0
    assert disruption(["a", "b"], ["a", "c"]) == 0.5
    assert disruption([], []) == 0.0


def test_compare_reports_maglev_as_the_only_non_minimal_algorithm():
    reports = {r.name: r for r in compare(node_count=10, key_count=6_000)}
    assert len(reports) == 5
    for name, report in reports.items():
        if name == "MaglevHash":
            assert not report.is_minimally_disruptive
        else:
            assert report.is_minimally_disruptive, name
    # Every algorithm moves approximately the departing node's own share.
    for report in reports.values():
        assert report.moved == pytest.approx(report.victim_share, abs=0.02)
