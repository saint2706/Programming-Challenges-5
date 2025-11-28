import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consistent_hashing.hash_ring import HashRing, Sha256Hash


class SimpleHash:
    """Deterministic hash function for predictable tests."""

    def __init__(self, salt: str = ""):
        self.salt = salt

    def __call__(self, value: str) -> int:
        return hash((self.salt, value)) & ((1 << 64) - 1)


def test_ring_add_remove_and_lookup():
    ring = HashRing(hash_function=SimpleHash())
    ring.add_node("node-a", vnode_count=3)
    ring.add_node("node-b", vnode_count=2)

    assert len(ring.buckets) == 5
    assert list(ring.buckets) == sorted(ring.buckets, key=lambda bucket: bucket.hash)

    primary, replica = ring.lookup("sample-key", replicas=2)
    assert primary in {"node-a", "node-b"}
    assert replica in {"node-a", "node-b"}
    assert primary != replica

    ring.remove_node("node-b")
    assert all(bucket.node == "node-a" for bucket in ring.buckets)

    assert ring.lookup("sample-key", replicas=1) == ["node-a"]


def test_lookup_wraps_and_validates():
    ring = HashRing(hash_function=SimpleHash("wrap"))
    with pytest.raises(ValueError):
        ring.lookup("key")
    with pytest.raises(ValueError):
        ring.lookup("key", replicas=0)

    ring.add_node("only", vnode_count=1)
    assert ring.lookup("any", replicas=1) == ["only"]


@pytest.mark.parametrize("vnode_count", [25, 50])
def test_rebalancing_movement_is_limited(vnode_count: int):
    ring = HashRing(hash_function=Sha256Hash())
    nodes = ["n1", "n2", "n3"]
    for node in nodes:
        ring.add_node(node, vnode_count=vnode_count)

    keys = [f"key-{i}" for i in range(500)]
    before = {key: ring.lookup(key)[0] for key in keys}

    ring.add_node("n4", vnode_count=vnode_count)
    after = {key: ring.lookup(key)[0] for key in keys}

    moved = sum(1 for key in keys if before[key] != after[key])
    moved_ratio = moved / len(keys)

    # Adding one node to three should move roughly 25% of keys; allow slack for randomness.
    assert moved_ratio < 0.4


def test_removing_node_keeps_other_assignments_stable():
    ring = HashRing(hash_function=Sha256Hash())
    for node in ["a", "b", "c", "d"]:
        ring.add_node(node, vnode_count=30)

    keys = [f"k{i}" for i in range(300)]
    before = {key: ring.lookup(key)[0] for key in keys}

    ring.remove_node("c")
    after = {key: ring.lookup(key)[0] for key in keys}

    for key in keys:
        if before[key] == "c":
            assert after[key] != "c"
        else:
            assert after[key] == before[key]
