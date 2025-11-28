"""
Emulation/Modeling project implementation.
"""

import numpy as np

class CAEngine:
    """
    Generic 2D Cellular Automata Engine using numpy vectorization.
    Supports arbitrary B/S (Birth/Survival) rules.
    """
    def __init__(self, width, height, rule_b=(3,), rule_s=(2, 3)):
        """
        Initialize the grid.
        :param width: Grid width
        :param height: Grid height
        :param rule_b: Tuple of neighbor counts that cause birth (default Conway: 3)
        :param rule_s: Tuple of neighbor counts that cause survival (default Conway: 2, 3)
        """
        self.width = width
        self.height = height
        self.rule_b = np.array(list(rule_b))
        self.rule_s = np.array(list(rule_s))
        self.grid = np.zeros((height, width), dtype=np.int8)
        self.generation = 0

    def randomize(self, density=0.2):
        """Randomly populate the grid."""
        self.grid = (np.random.random((self.height, self.width)) < density).astype(np.int8)
        self.generation = 0

    def step(self):
        """Advance the simulation by one generation."""
        # Count neighbors using numpy rolling for toroidal boundary conditions
        # Neighbors = sum of 8 surrounding cells
        neighbors = (
            np.roll(self.grid, 1, axis=0) +  # N
            np.roll(self.grid, -1, axis=0) + # S
            np.roll(self.grid, 1, axis=1) +  # W
            np.roll(self.grid, -1, axis=1) + # E
            np.roll(np.roll(self.grid, 1, axis=0), 1, axis=1) +   # NW
            np.roll(np.roll(self.grid, 1, axis=0), -1, axis=1) +  # NE
            np.roll(np.roll(self.grid, -1, axis=0), 1, axis=1) +  # SW
            np.roll(np.roll(self.grid, -1, axis=0), -1, axis=1)   # SE
        )

        # Apply rules
        # Birth: Dead cell (0) with neighbor count in rule_b
        # isin is a bit slow, but flexible. For small rule sets, it's fine.
        birth_mask = (self.grid == 0) & np.isin(neighbors, self.rule_b)

        # Survival: Live cell (1) with neighbor count in rule_s
        survival_mask = (self.grid == 1) & np.isin(neighbors, self.rule_s)

        self.grid = (birth_mask | survival_mask).astype(np.int8)
        self.generation += 1

    def clear(self):
        """
        Docstring for clear.
        """
        self.grid.fill(0)
        self.generation = 0

    def set_cell(self, x, y, state):
        """
        Docstring for set_cell.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = state

    def toggle_cell(self, x, y):
        """
        Docstring for toggle_cell.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = 1 - self.grid[y, x]

    def set_rules(self, b_rules, s_rules):
        """
        Docstring for set_rules.
        """
        self.rule_b = np.array(list(b_rules))
        self.rule_s = np.array(list(s_rules))

    def get_state(self):
        """
        Docstring for get_state.
        """
        return self.grid
