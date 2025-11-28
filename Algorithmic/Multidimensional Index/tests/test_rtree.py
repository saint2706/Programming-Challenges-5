import os
import unittest

from rtree import Rect, RTree


class TestRTree(unittest.TestCase):
    def test_basic_ops(self):
        tree = RTree()
        # Insert (0,0) to (1,1)
        tree.insert(Rect(0, 0, 1, 1), "A")
        # Insert (5,5) to (6,6)
        tree.insert(Rect(5, 5, 6, 6), "B")

        # Search overlapping A
        res = tree.search(Rect(0, 0, 2, 2))
        self.assertIn("A", res)
        self.assertNotIn("B", res)

        # Search encompassing both
        res = tree.search(Rect(0, 0, 10, 10))
        self.assertIn("A", res)
        self.assertIn("B", res)

    def test_split_and_structure(self):
        # Force splits (MAX_ENTRIES=4)
        tree = RTree()
        for i in range(10):
            tree.insert(Rect(i, i, i + 1, i + 1), i)

        # Should have split into depth > 1
        # Root should not be leaf
        self.assertFalse(tree.root.is_leaf)

        # Query mid range
        res = tree.search(Rect(4, 4, 6, 6))
        # Should find 4 (4-5), 5 (5-6). 6 starts at 6, depends on intersection logic.
        # Rect(i,i,i+1,i+1) vs Rect(4,4,6,6)
        # i=3: 3-4. touches at 4? intersects usually yes.
        # i=4: 4-5. yes.
        # i=5: 5-6. yes.
        # i=6: 6-7. touches at 6? yes.
        self.assertIn(4, res)
        self.assertIn(5, res)

    def test_serialization(self):
        tree = RTree()
        tree.insert(Rect(0, 0, 1, 1), "Data")
        tree.save("test_rtree.json")

        tree2 = RTree()
        tree2.load("test_rtree.json")
        res = tree2.search(Rect(0, 0, 1, 1))
        self.assertEqual(res, ["Data"])

        if os.path.exists("test_rtree.json"):
            os.remove("test_rtree.json")


if __name__ == "__main__":
    unittest.main()
