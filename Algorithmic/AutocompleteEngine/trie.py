from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class TrieNode:
    """Node inside a Trie storing children and word frequency."""

    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_word: bool = False
    frequency: int = 0

    def to_dict(self) -> dict:
        """Serialize node to a JSON-friendly dict."""
        return {
            "is_word": self.is_word,
            "frequency": self.frequency,
            "children": {char: child.to_dict() for char, child in self.children.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrieNode":
        node = cls(is_word=data.get("is_word", False), frequency=data.get("frequency", 0))
        node.children = {char: cls.from_dict(child) for char, child in data.get("children", {}).items()}
        return node


class AutocompleteEngine:
    """Trie-backed autocomplete engine with persistence and ranking support."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str, frequency: int = 1) -> None:
        """Insert a word into the Trie, incrementing its frequency.

        Args:
            word: Word to insert. Case is preserved and treated distinctly.
            frequency: Amount to increment the word's stored frequency by.
        """
        if not word:
            return

        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True
        node.frequency += max(frequency, 0)

    def _find_node(self, prefix: str) -> TrieNode | None:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _collect(self, node: TrieNode, prefix: str, results: List[Tuple[str, int]]) -> None:
        if node.is_word:
            results.append((prefix, node.frequency))
        for char, child in node.children.items():
            self._collect(child, prefix + char, results)

    def top_k(self, prefix: str, k: int) -> List[str]:
        """Return up to ``k`` completions for ``prefix`` sorted by frequency then lexicographically."""
        start = self._find_node(prefix)
        if start is None or k <= 0:
            return []

        results: List[Tuple[str, int]] = []
        self._collect(start, prefix, results)
        results.sort(key=lambda item: (-item[1], item[0]))
        return [word for word, _ in results[:k]]

    def to_json(self, path: str | Path) -> None:
        """Persist the Trie to a JSON file."""
        data = self.root.to_dict()
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def from_json(cls, path: str | Path) -> "AutocompleteEngine":
        """Load an engine from a JSON file produced by :meth:`to_json`."""
        engine = cls()
        content = Path(path).read_text()
        engine.root = TrieNode.from_dict(json.loads(content))
        return engine
