"""
Implementation of the algorithm.
"""

import unittest
from label_placement import Label, MapLabeler, intersect

class TestLabelPlacement(unittest.TestCase):
    """
    Docstring for TestLabelPlacement.
    """
    def test_intersection(self):
        # (0, 0, 10, 10)
        """
        Docstring for test_intersection.
        """
        r1 = (0, 0, 10, 10)
        # (5, 5, 15, 15) -> Intersects
        r2 = (5, 5, 15, 15)
        # (11, 11, 20, 20) -> No intersection
        r3 = (11, 11, 20, 20)

        self.assertTrue(intersect(r1, r2))
        self.assertFalse(intersect(r1, r3))

    def test_energy_calculation(self):
        # Two labels at same point, overlapping
        """
        Docstring for test_energy_calculation.
        """
        l1 = Label("A", 10, 10, 10, 10)
        l2 = Label("B", 10, 10, 10, 10)

        # Both default to pos 0 (TopRight) -> Overlap
        solver = MapLabeler([l1, l2], (0, 0, 100, 100))
        e1 = solver.energy()
        self.assertTrue(e1 > 0)

        # Move l2 to BottomLeft (pos 3) -> No overlap
        # l1: (10.5, 10.5, 20.5, 20.5)
        # l2: (0-.5, ..., 10-.5, 10-.5) -> (0, 0, 9.5, 9.5) roughly
        # No overlap.
        l2.set_position(3)
        e2 = solver.energy()

        # e2 should be smaller than e1 (unless preference weight for pos 3 is huge, but overlap weight is usually dominant)
        self.assertLess(e2, e1)

    def test_solve_improves_energy(self):
        # Create a crowded scenario
        """
        Docstring for test_solve_improves_energy.
        """
        labels = [Label("L", 50, 50, 10, 10) for _ in range(4)]
        # All at same point, will heavily overlap
        solver = MapLabeler(labels, (0, 0, 100, 100))
        initial_e = solver.energy()

        final_e = solver.solve(iterations=1000)
        self.assertLess(final_e, initial_e)

if __name__ == '__main__':
    unittest.main()
