import unittest
import numpy as np
from ca_engine import CAEngine

class TestCAEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CAEngine(10, 10, rule_b=(3,), rule_s=(2, 3))

    def test_blinker_oscillator(self):
        """Test the standard Blinker oscillator in Game of Life."""
        # Initial state (horizontal line of 3)
        # 0 0 0
        # 1 1 1
        # 0 0 0
        self.engine.set_cell(5, 5, 1)
        self.engine.set_cell(4, 5, 1)
        self.engine.set_cell(6, 5, 1)

        # Step 1: Should become vertical
        # 0 1 0
        # 0 1 0
        # 0 1 0
        self.engine.step()

        # Check center column (x=5) has alive cells at y=4,5,6
        self.assertEqual(self.engine.grid[4, 5], 1)
        self.assertEqual(self.engine.grid[5, 5], 1)
        self.assertEqual(self.engine.grid[6, 5], 1)

        # Check sides died (row y=5, x=4 and x=6)
        self.assertEqual(self.engine.grid[5, 4], 0)
        self.assertEqual(self.engine.grid[5, 6], 0)

        # Step 2: Should return to horizontal
        self.engine.step()
        self.assertEqual(self.engine.grid[5, 4], 1)
        self.assertEqual(self.engine.grid[5, 5], 1)
        self.assertEqual(self.engine.grid[5, 6], 1)
        self.assertEqual(self.engine.grid[4, 5], 0)

    def test_block_still_life(self):
        """Test the Block still life (stable 2x2 square)."""
        self.engine.set_cell(1, 1, 1)
        self.engine.set_cell(1, 2, 1)
        self.engine.set_cell(2, 1, 1)
        self.engine.set_cell(2, 2, 1)

        initial_state = self.engine.grid.copy()
        self.engine.step()

        np.testing.assert_array_equal(self.engine.grid, initial_state)

    def test_rule_change_highlife(self):
        """Test HighLife replicator rule (B36/S23)."""
        # Set HighLife
        self.engine.set_rules((3, 6), (2, 3))

        # 3 cells in a line (Blinker) behaves same as Life for one step
        self.engine.set_cell(4, 5, 1)
        self.engine.set_cell(5, 5, 1)
        self.engine.set_cell(6, 5, 1)
        self.engine.step()
        # Should be vertical
        self.assertEqual(self.engine.grid[5, 4], 0)
        self.assertEqual(self.engine.grid[4, 5], 1)

        # Test Birth on 6 neighbors
        self.engine.clear()
        # Create a configuration where a dead cell has 6 neighbors
        # 1 1 1
        # 1 0 1
        # 0 1 0
        coords = [(0,0), (0,1), (0,2), (1,0), (1,2), (2,1)]
        for r, c in coords:
            self.engine.set_cell(c, r, 1)

        self.assertEqual(self.engine.grid[1, 1], 0) # Target cell is dead
        self.engine.step()
        self.assertEqual(self.engine.grid[1, 1], 1) # Target cell should be born (6 neighbors)

if __name__ == '__main__':
    unittest.main()
