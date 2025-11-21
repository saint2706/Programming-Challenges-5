import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Algorithmic.TopKFrequentItems.misra_gries import (
    FrequentItem,
    MisraGriesCounter,
    SpaceSavingCounter,
)


def test_misra_gries_heavy_hitters():
    counter = MisraGriesCounter(k=4)
    stream = ["a"] * 40 + ["b"] * 30 + ["c"] * 20 + ["d"] * 10 + ["noise" + str(i) for i in range(50)]
    for item in stream:
        counter.update(item)

    hitters = counter.heavy_hitters(min_fraction=0.2)
    assert hitters[0].item == "a"
    assert hitters[0].estimate >= 40 - (counter.total // counter.k)
    # Memory bound: only k-1 counters kept
    assert len(counter.counters) <= counter.k - 1


def test_misra_gries_adversarial_stream():
    counter = MisraGriesCounter(k=5)
    # Flood with unique items to trigger decrements
    for i in range(200):
        counter.update(f"u{i}")
    assert len(counter.counters) <= 4

    for _ in range(60):
        counter.update("heavy")
    hitters = counter.heavy_hitters(min_fraction=0.25)
    assert hitters and hitters[0].item == "heavy"
    assert hitters[0].estimate >= 60 - (counter.total // counter.k)


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
