"""Visualization of 2D Geometry Operations using Manim.

Demonstrates Convex Hull (Graham Scan) and Line Intersection.
"""

import os
import sys
import math

from manim import *

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class ConvexHullDemo(Scene):
    """Manim Scene for demonstrating Graham Scan Convex Hull."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Convex Hull (Graham Scan)", font_size=32)
        title.to_edge(UP)
        self.play(Write(title))

        # Points
        points = [
            (-3, -1),
            (-2, 2),
            (-1, -2),
            (0, 0),
            (1, 2),
            (2, -1),
            (3, 1),
            (0.5, -1.5),
        ]

        # Create point dots
        dots = VGroup()
        labels = VGroup()
        for i, (x, y) in enumerate(points):
            dot = Dot(point=[x, y, 0], color=WHITE)
            label = Text(f"P{i}", font_size=12).next_to(dot, UR, buff=0.1)
            dots.add(dot)
            labels.add(label)

        self.play(Create(dots), Write(labels), run_time=1)
        self.wait(0.5)

        # Step 1: Find lowest point (anchor)
        info = Text("Step 1: Find lowest point", font_size=20, color=YELLOW)
        info.to_edge(LEFT).shift(UP * 2)
        self.play(Write(info))

        # Find lowest (lowest y, then leftmost x)
        anchor_idx = min(range(len(points)), key=lambda i: (points[i][1], points[i][0]))
        self.play(dots[anchor_idx].animate.set_color(RED).scale(1.5), run_time=0.5)

        anchor = points[anchor_idx]

        # Step 2: Sort by polar angle
        info2 = Text("Step 2: Sort by polar angle", font_size=20, color=YELLOW)
        info2.next_to(info, DOWN, aligned_edge=LEFT)
        self.play(Write(info2))

        def polar_angle(p):
            return math.atan2(p[1] - anchor[1], p[0] - anchor[0])

        sorted_indices = sorted(
            range(len(points)), key=lambda i: polar_angle(points[i])
        )

        # Draw lines from anchor showing angles
        angle_lines = VGroup()
        for idx in sorted_indices:
            if idx != anchor_idx:
                line = DashedLine(
                    start=[anchor[0], anchor[1], 0],
                    end=[points[idx][0], points[idx][1], 0],
                    color=GRAY,
                    dash_length=0.1,
                )
                angle_lines.add(line)
        self.play(Create(angle_lines), run_time=1)
        self.wait(0.5)

        # Step 3: Build hull
        info3 = Text("Step 3: Build hull (CCW turns)", font_size=20, color=YELLOW)
        info3.next_to(info2, DOWN, aligned_edge=LEFT)
        self.play(Write(info3))

        self.play(FadeOut(angle_lines))

        # Graham scan
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        hull = []
        hull_lines = VGroup()

        for idx in sorted_indices:
            p = points[idx]

            # While turn is clockwise, pop
            while len(hull) > 1 and cross(hull[-2], hull[-1], p) <= 0:
                # Remove point (animate)
                if hull_lines:
                    self.play(hull_lines[-1].animate.set_color(RED), run_time=0.2)
                    self.play(FadeOut(hull_lines[-1]), run_time=0.2)
                    hull_lines.remove(hull_lines[-1])
                hull.pop()

            # Add point
            if hull:
                new_line = Line(
                    start=[hull[-1][0], hull[-1][1], 0],
                    end=[p[0], p[1], 0],
                    color=GREEN,
                )
                hull_lines.add(new_line)
                self.play(Create(new_line), run_time=0.3)

            hull.append(p)
            # Highlight current point
            self.play(dots[idx].animate.set_color(GREEN), run_time=0.2)

        # Close the hull
        if len(hull) > 2:
            closing_line = Line(
                start=[hull[-1][0], hull[-1][1], 0],
                end=[hull[0][0], hull[0][1], 0],
                color=GREEN,
            )
            hull_lines.add(closing_line)
            self.play(Create(closing_line), run_time=0.3)

        # Final result
        result = Text(f"Hull has {len(hull)} vertices", font_size=24, color=GREEN)
        result.to_edge(DOWN)
        self.play(Write(result))

        self.wait(2)


if __name__ == "__main__":
    pass
