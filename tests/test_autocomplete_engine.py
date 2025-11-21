import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Algorithmic.AutocompleteEngine.trie import AutocompleteEngine


def test_top_k_orders_by_frequency_then_lexicographic():
    engine = AutocompleteEngine()
    engine.insert("apple", frequency=3)
    engine.insert("app", frequency=5)
    engine.insert("application", frequency=5)
    engine.insert("appetite", frequency=2)

    assert engine.top_k("app", 3) == ["app", "application", "apple"]


def test_unicode_and_case_sensitivity():
    engine = AutocompleteEngine()
    engine.insert("Café", frequency=4)
    engine.insert("café", frequency=1)
    engine.insert("caféteria", frequency=3)
    engine.insert("CAFÉ", frequency=2)

    assert engine.top_k("C", 5) == ["Café", "CAFÉ"]
    assert engine.top_k("caf", 5) == ["caféteria", "café"]
    assert engine.top_k("CAF", 5) == ["CAFÉ"]


def test_persistence_round_trip(tmp_path: Path):
    engine = AutocompleteEngine()
    engine.insert("hello", frequency=2)
    engine.insert("helium", frequency=1)
    engine.insert("héllo", frequency=4)

    json_path = tmp_path / "autocomplete.json"
    engine.to_json(json_path)

    data = json.loads(json_path.read_text())
    assert "children" in data

    restored = AutocompleteEngine.from_json(json_path)
    assert restored.top_k("hel", 2) == ["hello", "helium"]
    assert restored.top_k("hé", 1) == ["héllo"]


def test_top_k_handles_missing_prefix():
    engine = AutocompleteEngine()
    engine.insert("test", frequency=1)
    assert engine.top_k("toast", 3) == []


def test_inserting_zero_frequency_does_not_decrease_count():
    engine = AutocompleteEngine()
    engine.insert("repeat", frequency=2)
    engine.insert("repeat", frequency=0)
    assert engine.top_k("rep", 1) == ["repeat"]
