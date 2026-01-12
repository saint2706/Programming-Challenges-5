import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Algorithmic.RandomizedAlgorithmsSuite import (  # noqa: E402
    SkipList,
    Treap,
    benchmark_quickselect,
    quickselect,
)


def test_quickselect_correctness_and_inplace():
    rng = random.Random(42)
    data = [rng.randint(0, 1000) for _ in range(101)]
    copy = list(data)
    k = 50
    selected = quickselect(copy, k, rng=rng)
    assert selected == sorted(data)[k]
    assert set(copy) == set(data)  # in-place partition preserves multiset


def test_quickselect_benchmark_average_time_positive():
    rng = random.Random(123)
    result = benchmark_quickselect(trials=10, size=200, rng=rng)
    assert result.iterations == 10
    assert result.average_time > 0


def test_skiplist_operations_and_height():
    rng = random.Random(99)
    skiplist = SkipList(p=0.5, max_level=32, rng=rng)
    values = list(range(100))
    rng.shuffle(values)
    for v in values:
        skiplist.insert(v, v * 2)

    assert list(skiplist.keys()) == sorted(values)
    for v in values[:10]:
        assert skiplist.search(v) == v * 2
    for v in values[:10]:
        assert skiplist.delete(v) is True
        assert skiplist.search(v) is None

    expected_max_height = 3 * math.ceil(math.log2(len(values) + 1))
    assert skiplist.level <= expected_max_height


def test_treap_invariants_and_height():
    rng = random.Random(7)
    treap = Treap(rng=rng)
    items = list(range(200))
    rng.shuffle(items)
    for item in items:
        treap.insert(item, item)

    inorder_keys = [node.key for node in treap.inorder()]
    assert inorder_keys == sorted(items)

    def verify_heap_property(node):
        if node is None:
            return True
        if node.left and node.left.priority < node.priority:
            return False
        if node.right and node.right.priority < node.priority:
            return False
        return verify_heap_property(node.left) and verify_heap_property(node.right)

    assert verify_heap_property(treap.root)

    expected_height_cap = 4 * math.ceil(math.log2(len(items) + 1))
    assert treap.height() <= expected_height_cap

    # deletion should maintain properties
    for key in items[:20]:
        treap.delete(key)
    remaining_keys = [node.key for node in treap.inorder()]
    assert remaining_keys == sorted(items[20:])
    assert verify_heap_property(treap.root)
