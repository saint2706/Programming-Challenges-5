"""Skip List implementation.

A probabilistic data structure that provides O(log n) average complexity for
search, insert, and delete operations, similar to balanced trees but simpler to implement.
"""

from __future__ import annotations

import random
from typing import Any, Generator, Iterator, List, Optional, Tuple


class SkipListNode:
    """A node in the Skip List.

    Attributes:
        key: The key stored in the node (must be comparable).
        value: The value associated with the key.
        forward: List of pointers to next nodes at various levels.
    """

    def __init__(self, key: Any, value: Any, level: int) -> None:
        """Initialize a new Skip List Node.

        Args:
            key: Key for sorting.
            value: Value to store.
            level: The maximum level this node appears in (0-indexed).
        """
        self.key = key
        self.value = value
        # Forward pointers for levels 0 to level
        self.forward: List[Optional[SkipListNode]] = [None] * (level + 1)


class SkipList:
    """Probabilistic skip list supporting search, insert, and delete.

    The list is sorted by key.
    """

    def __init__(
        self,
        p: float = 0.5,
        max_level: int = 32,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize a Skip List.

        Args:
            p: Probability of promoting a node to the next level (default 0.5).
            max_level: Maximum number of levels allowed (default 32).
            rng: Optional random number generator for reproducibility.
        """
        self.p = p
        self.max_level = max_level
        self.level = 0  # Current maximum level in the list
        # Header node does not store data but anchors pointers
        self.header = SkipListNode(None, None, self.max_level)
        self._rng = rng or random.Random()

    def _random_level(self) -> int:
        """Generate a random level for a new node.

        Returns:
            int: Random level between 0 and max_level.
        """
        lvl = 0
        while self._rng.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def search(self, key: Any) -> Optional[Any]:
        """Search for a value by key.

        Args:
            key: The key to search for.

        Returns:
            Optional[Any]: The value if found, else None.
        """
        current = self.header
        # Start from top level and move down/right
        for i in reversed(range(self.level + 1)):
            while True:
                next_node = current.forward[i]
                # Check if next node exists and has a key less than search key
                # We must be careful with the header node which has key=None (treated as -inf ideally, but here we skip comparison if key is None or handle logic)
                # Ideally header.key is None. Regular nodes have valid keys.
                if next_node and next_node.key is not None and next_node.key < key:
                    current = next_node
                else:
                    break

        # Move to level 0
        current = current.forward[0]  # type: ignore
        if current and current.key == key:
            return current.value
        return None

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the list.

        If the key already exists, its value is updated.

        Args:
            key: The key to insert.
            value: The value to associate with the key.
        """
        # Track the path to update pointers
        update: List[SkipListNode] = [self.header] * (self.max_level + 1)
        current = self.header

        for i in reversed(range(self.level + 1)):
            while True:
                next_node = current.forward[i]
                if next_node and next_node.key is not None and next_node.key < key:
                    current = next_node
                else:
                    break
            update[i] = current

        current = current.forward[0]  # type: ignore

        # Update existing key
        if current and current.key == key:
            current.value = value
            return

        # Insert new node
        lvl = self._random_level()

        # If new level is higher than current max, initialize update array
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.header
            self.level = lvl

        new_node = SkipListNode(key, value, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node

    def delete(self, key: Any) -> bool:
        """Delete a node by key.

        Args:
            key: The key to delete.

        Returns:
            bool: True if the key was found and deleted, False otherwise.
        """
        update: List[SkipListNode] = [self.header] * (self.max_level + 1)
        current = self.header

        for i in reversed(range(self.level + 1)):
            while True:
                next_node = current.forward[i]
                if next_node and next_node.key is not None and next_node.key < key:
                    current = next_node
                else:
                    break
            update[i] = current

        current = current.forward[0]  # type: ignore

        if current and current.key == key:
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]

            # Reduce level if top layers are empty
            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            return True
        return False

    def __iter__(self) -> Iterator[Tuple[Any, Any]]:
        """Iterate over the list in sorted order.

        Yields:
            Tuple[Any, Any]: (key, value) pairs.
        """
        node = self.header.forward[0]
        while node:
            yield node.key, node.value
            node = node.forward[0]

    def keys(self) -> Generator[Any, None, None]:
        """Generate keys in sorted order.

        Yields:
            Any: Keys.
        """
        for key, _ in self:
            yield key

    def values(self) -> Generator[Any, None, None]:
        """Generate values in sorted order.

        Yields:
            Any: Values.
        """
        for _, value in self:
            yield value
