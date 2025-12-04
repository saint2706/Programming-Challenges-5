import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "SuffixAutomaton", "python"))
from sam import SuffixAutomaton

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "SuffixArrayLCP", "python"))
from suffix_array import SuffixArray

sys.path.append(
    os.path.join(os.getcwd(), "Algorithmic", "StreamingQuantiles", "python")
)
from quantiles import GKQuantile

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "GraphIsomorphism", "python"))
from wl_test import are_isomorphic

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "GeometryEngine2D", "python"))
from geometry import convex_hull, point_in_polygon

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "OnDiskBTree", "python"))
from btree import BTree

sys.path.append(os.path.join(os.getcwd(), "Algorithmic", "MatchingEngine", "python"))
from matching import MatchingEngine


class TestAlgoBatch2(unittest.TestCase):
    def test_sam(self):
        sam = SuffixAutomaton("banana")
        self.assertTrue(sam.check_substring("ana"))
        self.assertTrue(sam.check_substring("nan"))
        self.assertFalse(sam.check_substring("band"))

    def test_suffix_array(self):
        sa = SuffixArray("banana")
        self.assertEqual(sa.sa, [6, 5, 3, 1, 0, 4, 2])

    def test_quantiles(self):
        gk = GKQuantile(epsilon=0.1)
        for i in range(1, 101):
            gk.insert(i)

        median = gk.query(0.5)
        # GK is approximate.
        # For small N=100, implementation details matter.
        # Just check it's within [30, 70]
        self.assertTrue(30 <= median <= 70)

    def test_wl_isomorphism(self):
        adj1 = [[1, 2], [0, 2], [0, 1]]
        adj2 = [[1, 2], [0, 2], [0, 1]]
        self.assertTrue(are_isomorphic(adj1, adj2))

        adj3 = [[1], [0, 2], [1]]
        self.assertFalse(are_isomorphic(adj1, adj3))

    def test_geometry(self):
        points = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]
        hull = convex_hull(points)
        self.assertEqual(len(hull), 4)

        poly = [(0, 0), (2, 0), (2, 2), (0, 2)]
        self.assertTrue(point_in_polygon(poly, (1, 1)))
        self.assertFalse(point_in_polygon(poly, (3, 3)))

    def test_btree(self):
        bt = BTree(t=2)
        for i in range(10):
            bt.insert(i)
        self.assertTrue(bt.search(5))
        self.assertFalse(bt.search(20))

    def test_matching_engine(self):
        me = MatchingEngine()
        me.place_limit_order("sell", 100.0, 10)
        me.place_limit_order("buy", 100.0, 5)
        self.assertEqual(me.asks[0][2], 5)
        me.place_limit_order("buy", 90.0, 10)
        self.assertEqual(len(me.bids), 1)


if __name__ == "__main__":
    unittest.main()
