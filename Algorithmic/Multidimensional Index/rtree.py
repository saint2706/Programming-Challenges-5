import json
import os
from typing import Any, List, Optional

# Constants
MAX_ENTRIES = 4
MIN_ENTRIES = 2


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def area(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def contains(self, other: "Rect") -> bool:
        return (
            self.x1 <= other.x1
            and self.x2 >= other.x2
            and self.y1 <= other.y1
            and self.y2 >= other.y2
        )

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x2 < other.x1
            or self.x1 > other.x2
            or self.y2 < other.y1
            or self.y1 > other.y2
        )

    def union(self, other: "Rect") -> "Rect":
        return Rect(
            min(self.x1, other.x1),
            min(self.y1, other.y1),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
        )

    def to_dict(self):
        return [self.x1, self.y1, self.x2, self.y2]

    @staticmethod
    def from_dict(d):
        return Rect(d[0], d[1], d[2], d[3])

    def __repr__(self):
        return f"[{self.x1}, {self.y1}, {self.x2}, {self.y2}]"


class RTreeNode:
    def __init__(self, is_leaf=True):
        self.is_leaf = is_leaf
        self.rects: List[Rect] = []
        self.children: List[Any] = (
            []
        )  # If leaf: data IDs/Objects. If node: RTreeNode objects (or IDs if disk)
        self.parent: Optional["RTreeNode"] = None
        self.mbr: Optional[Rect] = None

    def update_mbr(self):
        if not self.rects:
            self.mbr = Rect(0, 0, 0, 0)
            return

        u = self.rects[0]
        for r in self.rects[1:]:
            u = u.union(r)
        self.mbr = u


class RTree:
    """
    In-memory R-Tree implementation.
    Serialization to disk is implemented via save/load whole tree.
    (True on-disk R-tree manages pages, but this is sufficient for the challenge scope).
    """

    def __init__(self):
        self.root = RTreeNode(is_leaf=True)

    def insert(self, rect: Rect, data: Any):
        leaf = self._choose_leaf(self.root, rect)
        self._add_entry(leaf, rect, data)

        if len(leaf.children) > MAX_ENTRIES:
            self._split_node(leaf)

    def search(self, query_rect: Rect) -> List[Any]:
        results = []
        self._search_recursive(self.root, query_rect, results)
        return results

    def _search_recursive(self, node: RTreeNode, query_rect: Rect, results: List[Any]):
        if not node.mbr or not node.mbr.intersects(query_rect):
            # Optimization: Check root MBR first?
            # Actually, node.mbr is the MBR of *this* node's entries.
            # But wait, usually search checks intersection with children's MBRs.
            pass

        if node.is_leaf:
            for i, r in enumerate(node.rects):
                if query_rect.intersects(r):
                    results.append(node.children[i])
        else:
            for i, r in enumerate(node.rects):
                if query_rect.intersects(r):
                    child = node.children[i]
                    self._search_recursive(child, query_rect, results)

    def _choose_leaf(self, node: RTreeNode, rect: Rect) -> RTreeNode:
        if node.is_leaf:
            return node

        # Choose child that requires least enlargement
        best_child = None
        min_enlargement = float("inf")

        for i, child_rect in enumerate(node.rects):
            union = child_rect.union(rect)
            enlargement = union.area() - child_rect.area()

            if enlargement < min_enlargement:
                min_enlargement = enlargement
                best_child = node.children[i]
            elif enlargement == min_enlargement:
                # Tie-breaker: smallest area
                if child_rect.area() < best_child.mbr.area():
                    best_child = node.children[i]

        return self._choose_leaf(best_child, rect)

    def _add_entry(self, node: RTreeNode, rect: Rect, child: Any):
        node.rects.append(rect)
        node.children.append(child)
        node.update_mbr()
        # Propagate MBR update up?
        # In this simplified version, MBRs in parent point to child.mbr.
        # But parent's `rects` list contains `child.mbr`. We need to update that.
        # This implementation structure is a bit loose (in-memory pointer based).
        # A standard way: parent stores (MBR, child_ptr).
        # Here `node.rects[i]` is the MBR for `node.children[i]`.
        # When we add to leaf, we update leaf MBR, but we need to update parent's entry for this leaf.

        self._adjust_tree(node)

    def _adjust_tree(self, node: RTreeNode):
        # Recalculate MBR of node
        node.update_mbr()

        if node.parent:
            # Find entry in parent corresponding to this node and update it
            parent = node.parent
            for i, child in enumerate(parent.children):
                if child is node:
                    parent.rects[i] = node.mbr
                    break
            self._adjust_tree(parent)

    def _split_node(self, node: RTreeNode):
        # Quadratic split (simplified: just split half/half by x coord sort)
        # Linear or Quadratic split is standard. Let's do a simple sort split.

        entries = list(zip(node.rects, node.children))
        # Sort by x1
        entries.sort(key=lambda e: e[0].x1)

        mid = len(entries) // 2
        group1 = entries[:mid]
        group2 = entries[mid:]

        # Node becomes group1
        node.rects = [e[0] for e in group1]
        node.children = [e[1] for e in group1]
        node.update_mbr()

        # New node for group2
        new_node = RTreeNode(is_leaf=node.is_leaf)
        new_node.rects = [e[0] for e in group2]
        new_node.children = [e[1] for e in group2]
        new_node.update_mbr()

        if node.parent is None:
            # Create new root
            new_root = RTreeNode(is_leaf=False)
            self._add_entry(new_root, node.mbr, node)
            self._add_entry(new_root, new_node.mbr, new_node)
            self.root = new_root
            node.parent = new_root
            new_node.parent = new_root
        else:
            # Add new_node to parent
            new_node.parent = node.parent
            self._add_entry(node.parent, new_node.mbr, new_node)
            if len(node.parent.children) > MAX_ENTRIES:
                self._split_node(node.parent)

    # Serialization
    def save(self, filepath: str):
        data = self._serialize_node(self.root)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _serialize_node(self, node: RTreeNode):
        return {
            "is_leaf": node.is_leaf,
            "rects": [r.to_dict() for r in node.rects],
            "children": [
                self._serialize_node(c) if not node.is_leaf else c
                for c in node.children
            ],
        }

    def load(self, filepath: str):
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            data = json.load(f)
        self.root = self._deserialize_node(data)

    def _deserialize_node(self, data) -> RTreeNode:
        node = RTreeNode(is_leaf=data["is_leaf"])
        node.rects = [Rect.from_dict(r) for r in data["rects"]]
        if node.is_leaf:
            node.children = data["children"]
        else:
            node.children = [self._deserialize_node(c) for c in data["children"]]
            for c in node.children:
                c.parent = node
        node.update_mbr()
        return node
