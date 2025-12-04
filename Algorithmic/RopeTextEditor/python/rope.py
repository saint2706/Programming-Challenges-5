"""Rope Data Structure for efficient string editing.

A Rope is a binary tree where each leaf holds a string and each node holds the length
of the left child. This allows for fast concatenation and splitting.
"""

from typing import Optional, Tuple, Union


class RopeNode:
    __slots__ = ["left", "right", "value", "weight"]

    def __init__(
        self,
        value: str = "",
        left: Optional["RopeNode"] = None,
        right: Optional["RopeNode"] = None,
    ):
        self.value = value
        self.left = left
        self.right = right
        if left is None:
            self.weight = len(value)
        else:
            self.weight = left.length()

    def length(self) -> int:
        if self.left is None and self.right is None:
            return self.weight
        l = self.weight
        if self.right:
            l += self.right.length()
        return l

    def _collect(self) -> str:
        if self.left is None and self.right is None:
            return self.value
        s = ""
        if self.left:
            s += self.left._collect()
        if self.right:
            s += self.right._collect()
        return s


class Rope:
    def __init__(self, data: Union[str, RopeNode] = ""):
        if isinstance(data, str):
            self.root = RopeNode(data) if data else None
        else:
            self.root = data

    def __len__(self):
        return self.root.length() if self.root else 0

    def __str__(self):
        return self.root._collect() if self.root else ""

    def concat(self, other: "Rope") -> "Rope":
        if not self.root:
            return other
        if not other.root:
            return self
        new_root = RopeNode(left=self.root, right=other.root)
        return Rope(new_root)

    def index(self, i: int) -> str:
        if not self.root:
            raise IndexError("Index out of bounds")
        return self._index(self.root, i)

    def _index(self, node: RopeNode, i: int) -> str:
        if node.weight <= i:
            if node.right:
                return self._index(node.right, i - node.weight)
            else:
                raise IndexError("Index out of bounds")
        else:
            if node.left:
                return self._index(node.left, i)
            else:
                return node.value[i]

    def split(self, i: int) -> Tuple["Rope", "Rope"]:
        """Split rope at index i. Returns (left_rope, right_rope)."""
        if not self.root:
            return Rope(""), Rope("")
        if i == 0:
            return Rope(""), self
        if i >= len(self):
            return self, Rope("")

        l, r = self._split_node(self.root, i)
        return Rope(l), Rope(r)

    def _split_node(
        self, node: RopeNode, i: int
    ) -> Tuple[Optional[RopeNode], Optional[RopeNode]]:
        if node.left is None:  # Leaf
            # Split string value
            val = node.value
            return RopeNode(val[:i]), RopeNode(val[i:])

        if i < node.weight:
            # Split is in left child
            ll, lr = self._split_node(node.left, i)
            # Right part of split becomes (lr + node.right)
            new_right = RopeNode(left=lr, right=node.right) if lr else node.right
            return ll, new_right
        else:
            # Split is in right child
            rl, rr = self._split_node(node.right, i - node.weight)
            # Left part is (node.left + rl)
            new_left = RopeNode(left=node.left, right=rl)
            return new_left, rr

    def insert(self, i: int, s: str) -> "Rope":
        """Insert string s at index i."""
        left, right = self.split(i)
        middle = Rope(s)
        return left.concat(middle).concat(right)

    def delete(self, i: int, j: int) -> "Rope":
        """Delete from i to j (exclusive)."""
        left, right = self.split(i)
        _, remaining = self.split(
            j
        )  # Wait, split is destructive? No, it returns new nodes.
        # But split logic above assumes immutable structure?
        # Actually my split implementation creates new nodes for the path, so it's immutable-ish.
        # Let's re-split properly.
        # Split at j first
        l_part, r_part = self.split(j)
        # Split l_part at i
        ll, _ = l_part.split(i)
        return ll.concat(r_part)
