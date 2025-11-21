from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TreapNode:
    key: Any
    value: Any
    priority: float
    left: Optional["TreapNode"] = None
    right: Optional["TreapNode"] = None


class Treap:
    """Treap (tree + heap) keyed by priority for balancing."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.root: Optional[TreapNode] = None
        self._rng = rng or random.Random()

    def _rotate_right(self, y: TreapNode) -> TreapNode:
        x = y.left
        if x is None:
            return y
        y.left = x.right
        x.right = y
        return x

    def _rotate_left(self, x: TreapNode) -> TreapNode:
        y = x.right
        if y is None:
            return x
        x.right = y.left
        y.left = x
        return y

    def insert(self, key: Any, value: Any, priority: Optional[float] = None) -> None:
        priority = self._rng.random() if priority is None else priority
        self.root = self._insert(self.root, key, value, priority)

    def _insert(self, root: Optional[TreapNode], key: Any, value: Any, priority: float) -> TreapNode:
        if root is None:
            return TreapNode(key, value, priority)
        if key < root.key:
            root.left = self._insert(root.left, key, value, priority)
            if root.left and root.left.priority < root.priority:
                root = self._rotate_right(root)
        elif key > root.key:
            root.right = self._insert(root.right, key, value, priority)
            if root.right and root.right.priority < root.priority:
                root = self._rotate_left(root)
        else:
            root.value = value
            root.priority = priority
        return root

    def search(self, key: Any) -> Optional[Any]:
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return node.value
        return None

    def _merge(self, left: Optional[TreapNode], right: Optional[TreapNode]) -> Optional[TreapNode]:
        if not left or not right:
            return left or right
        if left.priority < right.priority:
            left.right = self._merge(left.right, right)
            return left
        right.left = self._merge(left, right.left)
        return right

    def delete(self, key: Any) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, root: Optional[TreapNode], key: Any) -> Optional[TreapNode]:
        if root is None:
            return None
        if key < root.key:
            root.left = self._delete(root.left, key)
        elif key > root.key:
            root.right = self._delete(root.right, key)
        else:
            root = self._merge(root.left, root.right)
        return root

    def inorder(self):
        def traverse(node: Optional[TreapNode]):
            if node:
                yield from traverse(node.left)
                yield node
                yield from traverse(node.right)

        yield from traverse(self.root)

    def height(self) -> int:
        def _height(node: Optional[TreapNode]) -> int:
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))

        return _height(self.root)
