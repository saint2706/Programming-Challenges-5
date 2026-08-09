import importlib
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

triangulate_polygon = importlib.import_module(
    "Algorithmic.Polygon Triangulation.triangulation"
).triangulate_polygon


class TestTriangulation(unittest.TestCase):
    def test_square(self):
        # Square: (0,0), (1,0), (1,1), (0,1)
        # Should result in 2 triangles.
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
        poly = [(0, 0), (1, 0), (0, 1)]
        tris = triangulate_polygon(poly)
        self.assertEqual(len(tris), 1)
        self.assertEqual(tris[0], (0, 1, 2))

    def test_concave_polygon(self):
        # "Pacman" shape
        # (0,0), (2,0), (1,1) [concave point], (2,2), (0,2)
        poly = [(0, 0), (2, 0), (1, 1), (2, 2), (0, 2)]  # Concave vertex
        tris = triangulate_polygon(poly)
        self.assertEqual(len(tris), 3)

    def test_empty(self):
        self.assertEqual(triangulate_polygon([]), [])


if __name__ == "__main__":
    unittest.main()
