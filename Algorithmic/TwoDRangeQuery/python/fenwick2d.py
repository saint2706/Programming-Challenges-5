"""2D Binary Indexed Tree (Fenwick Tree) for Range Sum Queries.

Supports point update and range sum in O(log N * log M).
"""

from typing import List

class FenwickTree2D:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.tree = [[0] * (cols + 1) for _ in range(rows + 1)]

    def update(self, row: int, col: int, delta: int):
        """Add delta to (row, col). 0-indexed."""
        i = row + 1
        while i <= self.rows:
            j = col + 1
            while j <= self.cols:
                self.tree[i][j] += delta
                j += j & (-j)
            i += i & (-i)

    def query(self, row: int, col: int) -> int:
        """Sum from (0,0) to (row, col)."""
        res = 0
        i = row + 1
        while i > 0:
            j = col + 1
            while j > 0:
                res += self.tree[i][j]
                j -= j & (-j)
            i -= i & (-i)
        return res

    def range_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Sum of rectangle defined by (r1, c1) top-left and (r2, c2) bottom-right."""
        return (self.query(r2, c2)
                - self.query(r1 - 1, c2)
                - self.query(r2, c1 - 1)
                + self.query(r1 - 1, c1 - 1))
