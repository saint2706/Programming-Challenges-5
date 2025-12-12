"""On-Disk B-Tree Index.

Simulates a B-Tree structure suitable for disk storage.
"""

# Implementing a simple in-memory B-Tree for demonstration.
# Full on-disk requires file handling (struct pack/unpack).

from typing import List, Optional


class BTreeNode:
    def __init__(self, leaf: bool = False):
        self.leaf = leaf
        self.keys: List[int] = []
        self.children: List[BTreeNode] = []


class BTree:
    def __init__(self, t: int = 2):
        self.root = BTreeNode(True)
        self.t = t  # Min degree

    def insert(self, k: int):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root)
            self._split_child(temp, 0)
            self._insert_non_full(temp, k)
        else:
            self._insert_non_full(root, k)

    def _insert_non_full(self, x: BTreeNode, k: int):
        i = len(x.keys) - 1
        if x.leaf:
            x.keys.append(0)
            while i >= 0 and k < x.keys[i]:
                x.keys[i + 1] = x.keys[i]
                i -= 1
            x.keys[i + 1] = k
        else:
            while i >= 0 and k < x.keys[i]:
                i -= 1
            i += 1
            if len(x.children[i].keys) == (2 * self.t) - 1:
                self._split_child(x, i)
                if k > x.keys[i]:
                    i += 1
            self._insert_non_full(x.children[i], k)

    def _split_child(self, x: BTreeNode, i: int):
        t = self.t
        y = x.children[i]
        z = BTreeNode(y.leaf)
        x.children.insert(i + 1, z)
        x.keys.insert(i, y.keys[t - 1])
        z.keys = y.keys[t : (2 * t) - 1]
        y.keys = y.keys[0 : t - 1]
        if not y.leaf:
            z.children = y.children[t : (2 * t)]
            y.children = y.children[0:t]

    def search(self, k: int, x: Optional[BTreeNode] = None) -> bool:
        if x is None:
            x = self.root
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        if i < len(x.keys) and k == x.keys[i]:
            return True
        if x.leaf:
            return False
        return self.search(k, x.children[i])
