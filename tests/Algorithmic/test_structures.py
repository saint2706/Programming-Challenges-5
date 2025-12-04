import os
import sys
import unittest

sys.path.append(
    os.path.join(os.getcwd(), "Algorithmic", "PersistentDataStructures", "python")
)
from persistent import PersistentMap

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "RopeTextEditor", "python"))
from rope import Rope

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "TwoDRangeQuery", "python"))
from fenwick2d import FenwickTree2D


class TestAdvancedStructures(unittest.TestCase):
    def test_persistent_map(self):
        v0 = PersistentMap()
        v1 = v0.set("a", 1)
        v2 = v1.set("b", 2)
        v3 = v2.set("a", 3)

        self.assertIsNone(v0.get("a"))
        self.assertEqual(v1.get("a"), 1)
        self.assertIsNone(v1.get("b"))
        self.assertEqual(v2.get("a"), 1)
        self.assertEqual(v2.get("b"), 2)
        self.assertEqual(v3.get("a"), 3)
        self.assertEqual(v3.get("b"), 2)

        # Check independence (v2 should not change)
        self.assertEqual(v2.get("a"), 1)

    def test_rope(self):
        r1 = Rope("Hello")
        r2 = Rope(" World")
        r3 = r1.concat(r2)

        self.assertEqual(str(r3), "Hello World")
        self.assertEqual(r3.index(0), "H")
        self.assertEqual(r3.index(6), "W")

    def test_fenwick2d(self):
        # 3x3
        # 1 0 0
        # 0 2 0
        # 0 0 3
        ft = FenwickTree2D(3, 3)
        ft.update(0, 0, 1)
        ft.update(1, 1, 2)
        ft.update(2, 2, 3)

        # Sum (0,0) to (1,1) -> 1+2 = 3
        self.assertEqual(ft.range_query(0, 0, 1, 1), 3)
        # Sum (1,1) to (2,2) -> 2+3 = 5
        self.assertEqual(ft.range_query(1, 1, 2, 2), 5)
        # Sum (0,0) to (2,2) -> 6
        self.assertEqual(ft.range_query(0, 0, 2, 2), 6)


if __name__ == "__main__":
    unittest.main()
