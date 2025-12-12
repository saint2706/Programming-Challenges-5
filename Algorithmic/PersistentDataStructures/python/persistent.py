"""Persistent Data Structures using Path Copying.

Implements a Persistent Binary Search Tree (Map).
Every update returns a new root, preserving previous versions.
"""

from typing import Any, Optional


class Node:
    __slots__ = ["key", "value", "left", "right"]

    def __init__(
        self,
        key: Any,
        value: Any,
        left: Optional["Node"] = None,
        right: Optional["Node"] = None,
    ):
        self.key = key
        self.value = value
        self.left = left
        self.right = right


class PersistentMap:
    """A persistent key-value store based on a balanced BST (AVL logic omitted for brevity, simple BST).

    For production, this should be an AVL or Red-Black tree.
    Here we demonstrate path copying.
    """

    def __init__(self, root: Optional[Node] = None):
        self.root = root

    def get(self, key: Any) -> Optional[Any]:
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return node.value
        return None

    def set(self, key: Any, value: Any) -> "PersistentMap":
        """Return a new PersistentMap with the key set to value."""
        new_root = self._insert(self.root, key, value)
        return PersistentMap(new_root)

    def _insert(self, node: Optional[Node], key: Any, value: Any) -> Node:
        if node is None:
            return Node(key, value)

        # Path Copying: Create copy of current node
        new_node = Node(node.key, node.value, node.left, node.right)

        if key < node.key:
            new_node.left = self._insert(node.left, key, value)
        elif key > node.key:
            new_node.right = self._insert(node.right, key, value)
        else:
            new_node.value = value

        return new_node
