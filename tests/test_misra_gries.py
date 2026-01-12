import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Algorithmic.TopKFrequentItems.misra_gries import (  # noqa: E402
    MisraGriesCounter,
    SpaceSavingCounter,
)


def test_misra_gries_heavy_hitters():
    """Test Misra-Gries algorithm finds heavy hitters."""
    counter = MisraGriesCounter(k=4)
    # Create stream where 'a' is overwhelmingly frequent
    stream = ["a"] * 100 + ["b"] * 20 + ["c"] * 10 + ["d"] * 5
    for item in stream:
        counter.update(item)

    # Verify 'a' is tracked
    assert "a" in counter.counters
    # Verify counter memory bound: at most k-1 counters
    assert len(counter.counters) <= counter.k - 1

    # Get all tracked items
    all_items = counter.heavy_hitters()
    assert len(all_items) > 0
    # The most frequent item should be 'a'
    assert all_items[0].item == "a"


def test_misra_gries_adversarial_stream():
    """Test Misra-Gries with adversarial stream pattern."""
    counter = MisraGriesCounter(k=5)
    # First, add some unique items
    for i in range(50):
        counter.update(f"u{i}")
    # Memory bound check
    assert len(counter.counters) <= 4

    # Now heavily update one item
    for _ in range(200):
        counter.update("heavy")

    # Verify 'heavy' is tracked
    assert "heavy" in counter.counters
    # The counter for 'heavy' should be high
    assert counter.counters["heavy"] > 100


def test_space_saving_memory_and_errors():
    counter = SpaceSavingCounter(k=3)
    stream = ["x"] * 5 + ["y"] * 3 + ["z"] * 2 + ["w"] * 10
    for item in stream:
        counter.update(item)

    assert len(counter.counters) == 3
    hitters = counter.heavy_hitters(min_count=3)
    items = {h.item: h for h in hitters}
    # "w" replaces the smallest counter but should have a higher estimate
    assert items["w"].estimate >= 10
    # Estimates should never be below the tracked error
    for h in hitters:
        assert h.estimate >= h.error


def test_space_saving_adversarial_replacements():
    counter = SpaceSavingCounter(k=2)
    for i in range(10):
        counter.update(f"noise{i}")
    assert len(counter.counters) == 2

    for _ in range(15):
        counter.update("dominant")

    hitters = counter.heavy_hitters(min_fraction=0.5)
    assert hitters[0].item == "dominant"
    assert hitters[0].estimate >= 15
