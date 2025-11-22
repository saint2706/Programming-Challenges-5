"""Treap (Tree + Heap) implementation.

A Treap is a randomized binary search tree that maintains both BST property (on keys)
and Heap property (on random priorities). This structure is balanced with high probability.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Optional, Generator, Iterator


@dataclass
class TreapNode:
    """A node in the Treap.

    Attributes:
        key: Search key (BST property).
        value: Data value.
        priority: Random priority (Heap property).
        left: Left child.
        right: Right child.
    """

    key: Any
    value: Any
    priority: float
    left: Optional["TreapNode"] = None
    right: Optional["TreapNode"] = None


class Treap:
    """Treap (tree + heap) keyed by priority for balancing.

    Operations have O(log n) expected complexity.
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        """Initialize an empty Treap.

        Args:
            rng: Optional random number generator.
        """
        self.root: Optional[TreapNode] = None
        self._rng = rng or random.Random()

    def _rotate_right(self, y: TreapNode) -> TreapNode:
        """Perform right rotation around y."""
        x = y.left
        if x is None:
            return y
        y.left = x.right
        x.right = y
        return x

    def _rotate_left(self, x: TreapNode) -> TreapNode:
        """Perform left rotation around x."""
        y = x.right
        if y is None:
            return x
        x.right = y.left
        y.left = x
        return y

    def insert(
        self, key: Any, value: Any, priority: Optional[float] = None
    ) -> None:
        """Insert a key-value pair into the Treap.

        Args:
            key: Comparison key.
            value: Stored value.
            priority: Optional fixed priority (mostly for testing).
                      If None, a random priority is generated.
        """
        priority = self._rng.random() if priority is None else priority
        self.root = self._insert(self.root, key, value, priority)

    def _insert(
        self,
        root: Optional[TreapNode],
        key: Any,
        value: Any,
        priority: float,
    ) -> TreapNode:
        """Recursive insert helper."""
        if root is None:
            return TreapNode(key, value, priority)

        if key < root.key:
            root.left = self._insert(root.left, key, value, priority)
            # Maintain max-heap property (higher priority is root)
            # Note: Some implementations use min-heap; both work.
            # Here we check if child priority < parent priority?
            # The code snippet logic: `if root.left.priority < root.priority: rotate`.
            # This implies Min-Heap property (smaller priority bubbles up).
            if root.left and root.left.priority < root.priority:
                root = self._rotate_right(root)
        elif key > root.key:
            root.right = self._insert(root.right, key, value, priority)
            if root.right and root.right.priority < root.priority:
                root = self._rotate_left(root)
        else:
            # Update existing key
            root.value = value
            # Optionally update priority, but standard is to keep it
            root.priority = priority
        return root

    def search(self, key: Any) -> Optional[Any]:
        """Search for a value by key.

        Args:
            key: The key to search for.

        Returns:
            Optional[Any]: The value if found, else None.
        """
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return node.value
        return None

    def _merge(
        self, left: Optional[TreapNode], right: Optional[TreapNode]
    ) -> Optional[TreapNode]:
        """Merge two treaps (assuming all keys in left < all keys in right)."""
        if not left or not right:
            return left or right

        # To maintain Min-Heap property:
        if left.priority < right.priority:
            left.right = self._merge(left.right, right)
            return left
        else:
            right.left = self._merge(left, right.left)
            return right

    def delete(self, key: Any) -> None:
        """Delete a key from the Treap.

        Args:
            key: The key to delete.
        """
        self.root = self._delete(self.root, key)

    def _delete(
        self, root: Optional[TreapNode], key: Any
    ) -> Optional[TreapNode]:
        """Recursive delete helper."""
        if root is None:
            return None
        if key < root.key:
            root.left = self._delete(root.left, key)
        elif key > root.key:
            root.right = self._delete(root.right, key)
        else:
            # Found node to delete: merge its children
            root = self._merge(root.left, root.right)
        return root

    def inorder(self) -> Generator[TreapNode, None, None]:
        """Generate nodes in in-order (sorted by key).

        Yields:
            TreapNode: Nodes in ascending key order.
        """
        def traverse(node: Optional[TreapNode]) -> Iterator[TreapNode]:
            if node:
                yield from traverse(node.left)
                yield node
                yield from traverse(node.right)

        yield from traverse(self.root)

    def height(self) -> int:
        """Calculate the height of the tree.

        Returns:
            int: Height of the tree.
        """
        def _height(node: Optional[TreapNode]) -> int:
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))

        return _height(self.root)
