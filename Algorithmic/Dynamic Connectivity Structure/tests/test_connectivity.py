import unittest
from dynamic_connectivity import DynamicConnectivity

class TestDynamicConnectivity(unittest.TestCase):
    def setUp(self):
        self.dc = DynamicConnectivity()

    def test_basic_connectivity(self):
        self.dc.add_edge('A', 'B')
        self.assertTrue(self.dc.connected('A', 'B'))
        self.assertFalse(self.dc.connected('A', 'C'))

        self.dc.add_edge('B', 'C')
        self.assertTrue(self.dc.connected('A', 'C'))

    def test_cycle_redundancy(self):
        # A-B-C
        self.dc.add_edge('A', 'B')
        self.dc.add_edge('B', 'C')
        # Add cycle A-C
        self.dc.add_edge('A', 'C')

        self.assertTrue(self.dc.connected('A', 'C'))

        # Remove B-C. A-C should still hold via edge (A, C)
        # Note: B-C was a tree edge (A-B, B-C). A-C was non-tree.
        # Removing B-C splits {A,B} and {C}.
        # Reconnect searches for edge between {A,B} and {C}. Finds (A, C).
        self.dc.remove_edge('B', 'C')

        self.assertTrue(self.dc.connected('A', 'C'))
        self.assertTrue(self.dc.connected('B', 'C')) # B->A->C

    def test_disconnect(self):
        self.dc.add_edge('1', '2')
        self.dc.remove_edge('1', '2')
        self.assertFalse(self.dc.connected('1', '2'))

    def test_complex_reconnect(self):
        # Square A-B-C-D-A
        self.dc.add_edge('A', 'B')
        self.dc.add_edge('B', 'C')
        self.dc.add_edge('C', 'D')
        self.dc.add_edge('D', 'A')

        # Remove A-B
        self.dc.remove_edge('A', 'B')
        self.assertTrue(self.dc.connected('A', 'B')) # Via A-D-C-B

        # Remove C-D
        self.dc.remove_edge('C', 'D')
        # Now we have path A-D and path B-C. No link between them?
        # A-D-C-B broken at C-D.
        # Edges left: (A,D), (B,C). No link between {A,D} and {B,C}.
        self.assertFalse(self.dc.connected('A', 'B'))

if __name__ == '__main__':
    unittest.main()
