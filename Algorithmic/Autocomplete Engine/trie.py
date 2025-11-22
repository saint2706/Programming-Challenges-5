"""Trie (Prefix Tree) implementation for efficient autocomplete.

This module provides a Trie data structure capable of inserting words,
searching for prefixes, and retrieving top-k completions based on frequency.
It also supports JSON persistence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union


@dataclass
class TrieNode:
    """Node inside a Trie storing children and word frequency.

    Attributes:
        children: Dictionary mapping characters to child nodes.
        is_word: True if this node represents the end of a valid word.
        frequency: The frequency count of the word ending at this node.
    """

    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_word: bool = False
    frequency: int = 0

    def to_dict(self) -> Dict[str, Union[bool, int, Dict]]:
        """Serialize node to a JSON-friendly dict.

        Returns:
            dict: The serialized node data.
        """
        return {
            "is_word": self.is_word,
            "frequency": self.frequency,
            "children": {
                char: child.to_dict() for char, child in self.children.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Union[bool, int, Dict]]) -> "TrieNode":
        """Deserialize a node from a dictionary.

        Args:
            data: The dictionary containing node data.

        Returns:
            TrieNode: The reconstructed node.
        """
        node = cls(
            is_word=bool(data.get("is_word", False)),
            frequency=int(data.get("frequency", 0)),  # type: ignore
        )
        children_data = data.get("children", {})
        if isinstance(children_data, dict):
            node.children = {
                char: cls.from_dict(child_data)  # type: ignore
                for char, child_data in children_data.items()
            }
        return node


class AutocompleteEngine:
    """Trie-backed autocomplete engine with persistence and ranking support.

    Supports inserting words with frequencies and retrieving top-k completions
    for a given prefix.
    """

    def __init__(self) -> None:
        """Initialize an empty Autocomplete Engine."""
        self.root = TrieNode()

    def insert(self, word: str, frequency: int = 1) -> None:
        """Insert a word into the Trie, incrementing its frequency.

        Args:
            word: Word to insert. Case is preserved and treated distinctly.
            frequency: Amount to increment the word's stored frequency by.
                       Must be non-negative.
        """
        if not word:
            return

        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True
        node.frequency += max(frequency, 0)

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Traverse the Trie to find the node corresponding to the prefix.

        Args:
            prefix: The prefix string to locate.

        Returns:
            Optional[TrieNode]: The node if found, else None.
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _collect(
        self, node: TrieNode, prefix: str, results: List[Tuple[str, int]]
    ) -> None:
        """Recursively collect all words extending from the given node.

        Args:
            node: The starting node.
            prefix: The string built so far to reach this node.
            results: List to append found (word, frequency) tuples to.
        """
        if node.is_word:
            results.append((prefix, node.frequency))
        for char, child in node.children.items():
            self._collect(child, prefix + char, results)

    def top_k(self, prefix: str, k: int) -> List[str]:
        """Return up to `k` completions for `prefix`.

        Results are sorted first by frequency (descending), then lexicographically (ascending).

        Args:
            prefix: The prefix to autocomplete.
            k: Maximum number of suggestions to return.

        Returns:
            List[str]: A list of suggested words.
        """
        start = self._find_node(prefix)
        if start is None or k <= 0:
            return []

        results: List[Tuple[str, int]] = []
        self._collect(start, prefix, results)
        # Sort by frequency desc, then word asc
        results.sort(key=lambda item: (-item[1], item[0]))
        return [word for word, _ in results[:k]]

    def to_json(self, path: Union[str, Path]) -> None:
        """Persist the Trie to a JSON file.

        Args:
            path: File path to save the JSON data to.
        """
        data = self.root.to_dict()
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "AutocompleteEngine":
        """Load an engine from a JSON file produced by :meth:`to_json`.

        Args:
            path: File path to load the JSON data from.

        Returns:
            AutocompleteEngine: The loaded engine.
        """
        engine = cls()
        content = Path(path).read_text()
        engine.root = TrieNode.from_dict(json.loads(content))
        return engine
