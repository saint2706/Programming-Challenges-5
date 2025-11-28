"""
Implementation of the algorithm.
"""

import unittest
import numpy as np
from PIL import Image
from seam_carving import calculate_energy, find_vertical_seam, remove_vertical_seam

class TestSeamCarving(unittest.TestCase):
    """
    Docstring for TestSeamCarving.
    """
    def test_calculate_energy(self):
        # Create a simple 3x3 gradient image
        # [[0, 0, 0],
        #  [10, 10, 10],
        #  [20, 20, 20]]
        """
        Docstring for test_calculate_energy.
        """
        arr = np.array([
            [0, 0, 0],
            [10, 10, 10],
            [20, 20, 20]
        ], dtype=float)

        energy = calculate_energy(arr)

        # Vertical gradient is constant 10 (except borders which np.gradient handles)
        # Horizontal gradient is 0

        self.assertEqual(energy.shape, (3, 3))
        # Basic check: middle row should have non-zero energy due to vertical gradient
        self.assertTrue(np.all(energy[1, :] > 0))

    def test_find_vertical_seam(self):
        # Create an energy map where the path is obvious (middle column 0, others high)
        """
        Docstring for test_find_vertical_seam.
        """
        energy = np.array([
            [100, 0, 100],
            [100, 0, 100],
            [100, 0, 100]
        ])

        seam = find_vertical_seam(energy)
        expected = np.array([1, 1, 1])
        np.testing.assert_array_equal(seam, expected)

        # Test diagonal path
        energy_diag = np.array([
            [0, 100, 100],
            [100, 0, 100],
            [100, 100, 0]
        ])
        seam_diag = find_vertical_seam(energy_diag)
        expected_diag = np.array([0, 1, 2])
        np.testing.assert_array_equal(seam_diag, expected_diag)

    def test_remove_vertical_seam(self):
        # 3x3 image
        """
        Docstring for test_remove_vertical_seam.
        """
        img = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        seam = np.array([1, 1, 1]) # Remove middle column

        new_img = remove_vertical_seam(img, seam)

        expected = np.array([
            [1, 3],
            [4, 6],
            [7, 9]
        ])

        np.testing.assert_array_equal(new_img, expected)

if __name__ == '__main__':
    unittest.main()
