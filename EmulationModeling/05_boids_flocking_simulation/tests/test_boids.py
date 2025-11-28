"""
Emulation/Modeling project implementation.
"""

import unittest
import numpy as np
from boids import Boid, Flock

class TestBoids(unittest.TestCase):
    """
    Docstring for TestBoids.
    """
    def test_boid_movement(self):
        """
        Docstring for test_boid_movement.
        """
        boid = Boid(100, 100, 200, 200)
        initial_pos = boid.position.copy()
        boid.velocity = np.array([1.0, 0.0]) # Moving right
        boid.update()

        self.assertTrue(np.allclose(boid.position, initial_pos + np.array([1.0, 0.0])))

    def test_boid_wrapping(self):
        """
        Docstring for test_boid_wrapping.
        """
        boid = Boid(199, 100, 200, 200)
        boid.velocity = np.array([2.0, 0.0]) # Should cross 200
        boid.update()

        self.assertLess(boid.position[0], 200)
        self.assertGreaterEqual(boid.position[0], 0)
        # 199 + 2 = 201 -> 201 % 200 = 1
        self.assertAlmostEqual(boid.position[0], 1.0)

    def test_separation_logic(self):
        # Two boids very close
        """
        Docstring for test_separation_logic.
        """
        b1 = Boid(100, 100, 200, 200)
        b2 = Boid(100.1, 100, 200, 200) # 0.1 dist

        # Zero velocity to isolate force
        b1.velocity = np.zeros(2)
        b2.velocity = np.zeros(2)

        boids = [b1, b2]
        force = b1.flock(boids)

        # Separation should push b1 away from b2 (left)
        # b2 is to the right of b1, so force should be negative X
        self.assertLess(force[0], 0)

if __name__ == '__main__':
    unittest.main()
