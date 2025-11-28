"""Visualization of the Knapsack Problem using Dynamic Programming.

This script demonstrates the classic 0/1 Knapsack problem solution using DP.
It animates the construction of the DP table.
"""

import os
import sys
from typing import Any, Dict, List

from manim import *  # type: ignore

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class GenericDPDemo(Scene):
    """Manim Scene for demonstrating Knapsack DP."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Generic DP Visualization (Knapsack)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Problem: Knapsack
        # Weights and Values for items
        weights = [1, 3, 4, 5]
        values = [1, 4, 5, 7]
        capacity = 7
        n = len(weights)

        # Create Table
        rows = n + 1
        cols = capacity + 1

        # Grid
        grid = VGroup()
        # Type hint for cells structure: List[List[Dict[str, Any]]]
        cells: List[List[Dict[str, Any]]] = [
            [{"square": None, "val": 0, "text": None} for _ in range(cols)]
            for _ in range(rows)
        ]

        cell_size = 0.6
        start_pos = UP * 1.5 + LEFT * 3

        # Headers (Columns: Capacity w)
        for j in range(cols):
            label = Text(str(j), font_size=16)
            label.move_to(start_pos + RIGHT * (j + 1) * cell_size + UP * cell_size)
            self.add(label)

        # Headers (Rows: Items)
        for i in range(rows):
            label_text = f"Item {i}" if i > 0 else "0"
            label = Text(label_text, font_size=16)
            # Adjust left offset for longer text
            label.move_to(
                start_pos + DOWN * (i + 1) * cell_size + LEFT * 1.5 * cell_size
            )
            self.add(label)

        # Initialize grid cells
        for i in range(rows):
            for j in range(cols):
                square = Square(side_length=cell_size).set_stroke(color=WHITE)
                square.move_to(
                    start_pos + RIGHT * (j + 1) * cell_size + DOWN * (i + 1) * cell_size
                )
                grid.add(square)
                cells[i][j]["square"] = square

        self.play(Create(grid))

        # DP Logic
        dp = [[0 for _ in range(cols)] for _ in range(rows)]

        for i in range(rows):
            for w in range(cols):
                if i == 0 or w == 0:
                    val = 0
                elif weights[i - 1] <= w:
                    val = max(
                        values[i - 1] + dp[i - 1][w - weights[i - 1]],
                        dp[i - 1][w],
                    )
                else:
                    val = dp[i - 1][w]

                dp[i][w] = val

                # Animate
                text = Text(str(val), font_size=16)
                text.move_to(cells[i][w]["square"].get_center())

                cells[i][w]["text"] = text

                # Highlight
                self.play(
                    cells[i][w]["square"].animate.set_fill(BLUE, opacity=0.5),
                    run_time=0.05,
                )
                self.add(text)
                self.play(
                    cells[i][w]["square"].animate.set_fill(opacity=0),
                    run_time=0.05,
                )

        self.wait(2)
