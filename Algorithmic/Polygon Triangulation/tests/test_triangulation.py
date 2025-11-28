"""
Implementation of the algorithm.
"""

import unittest
from triangulation import triangulate_polygon

class TestTriangulation(unittest.TestCase):
    """
    Docstring for TestTriangulation.
    """
    def test_square(self):
        # Square: (0,0), (1,0), (1,1), (0,1)
        # Should result in 2 triangles.
        """
        Docstring for test_square.
        """
        poly = [(0, 0), (1, 0), (1, 1), (0, 1)]
        tris = triangulate_polygon(poly)
        self.assertEqual(len(tris), 2)

        # Verify indices are valid
        for tri in tris:
            self.assertEqual(len(tri), 3)
            for idx in tri:
                self.assertTrue(0 <= idx < 4)

    def test_triangle(self):
        # Already a triangle
        """
        Docstring for test_triangle.
        """
        poly = [(0, 0), (1, 0), (0, 1)]
        tris = triangulate_polygon(poly)
        self.assertEqual(len(tris), 1)
        self.assertEqual(tris[0], (0, 1, 2))

    def test_concave_polygon(self):
        # "Pacman" shape
        # (0,0), (2,0), (1,1) [concave point], (2,2), (0,2)
        """
        Docstring for test_concave_polygon.
        """
        poly = [
            (0, 0),
            (2, 0),
            (1, 1), # Concave vertex
            (2, 2),
            (0, 2)
        ]
        tris = triangulate_polygon(poly)
        self.assertEqual(len(tris), 3)

    def test_empty(self):
        """
        Docstring for test_empty.
        """
        self.assertEqual(triangulate_polygon([]), [])

if __name__ == '__main__':
    unittest.main()
