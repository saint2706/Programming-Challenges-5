"""Visualization of K-d Tree construction using Manim.

This script visualizes how a K-d tree partitions a 2D space by recursively
splitting points along alternating axes (x and y).
"""

import os
import sys
from typing import Optional

from manim import *  # type: ignore

# Add parent directory to path to import kd_tree
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Ensure import works even if sys.path is messy
try:
    from kd_tree import KDNode, build_kd_tree  # type: ignore
except ImportError:
    # Dummy fallback for static analysis or if run isolated
    pass


class KDTreeConstruction(Scene):
    """Manim Scene for demonstrating K-d Tree construction."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("K-d Tree Construction", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Define points
        points = [
            (2, 3),
            (5, 4),
            (9, 6),
            (4, 7),
            (8, 1),
            (7, 2),
        ]

        # Create axes
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 10, 1],
            axis_config={"color": BLUE},
        ).scale(0.8)

        self.play(Create(axes))

        # Plot points
        dots = VGroup()
        for p in points:
            dot = Dot(axes.c2p(*p), color=RED)
            label = Text(f"({p[0]},{p[1]})", font_size=16).next_to(dot, UP)
            dots.add(dot)
            dots.add(label)

        self.play(FadeIn(dots))
        self.wait(1)

        # Recursive function to visualize splitting
        def visualize_split(
            node: Optional[KDNode],
            x_min: float,
            x_max: float,
            y_min: float,
            y_max: float,
            depth: int,
        ) -> None:
            if node is None:
                return

            # Determine axis (0=x, 1=y)
            # Note: This logic must match the build_kd_tree logic
            # If dims=2, depth % 2 matches axis
            axis = depth % 2
            point = node.point

            if axis == 0:  # Vertical split (x-axis)
                start = axes.c2p(point[0], y_min)
                end = axes.c2p(point[0], y_max)
                line = Line(start, end, color=YELLOW)
                self.play(Create(line), run_time=0.5)

                visualize_split(node.left, x_min, point[0], y_min, y_max, depth + 1)
                visualize_split(node.right, point[0], x_max, y_min, y_max, depth + 1)
            else:  # Horizontal split (y-axis)
                start = axes.c2p(x_min, point[1])
                end = axes.c2p(x_max, point[1])
                line = Line(start, end, color=GREEN)
                self.play(Create(line), run_time=0.5)

                visualize_split(node.left, x_min, x_max, y_min, point[1], depth + 1)
                visualize_split(node.right, x_min, x_max, point[1], y_max, depth + 1)

        # Build tree and visualize
        root = build_kd_tree(points)
        visualize_split(root, 0, 10, 0, 10, 0)

        self.wait(2)
