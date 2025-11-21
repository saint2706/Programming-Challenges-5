"""Visualization of Interval Scheduling using Manim.

This script demonstrates the Greedy Interval Scheduling algorithm (Unweighted).
Note: The main implementation in `main.py` solves the *Weighted* version using DP.
This visualization simplifies the problem to the unweighted case (finding the maximum
number of non-overlapping intervals) to allow for a clearer visual demonstration of
greedy choices.
"""

import sys
import os
from typing import List, Tuple, Optional, Union

from manim import *  # type: ignore

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class IntervalSchedulingDemo(Scene):
    """Manim Scene for demonstrating Greedy Interval Scheduling."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Interval Scheduling (Greedy)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Intervals (start, end)
        intervals: List[Tuple[int, int]] = [
            (1, 3),
            (2, 4),
            (3, 6),
            (5, 7),
            (6, 8),
            (8, 10),
        ]

        # Create number line
        number_line = NumberLine(
            x_range=[0, 12, 1],
            length=10,
            color=BLUE,
            include_numbers=False,
            label_direction=DOWN,
        )
        number_line.move_to(DOWN * 2)
        self.play(Create(number_line))

        # Add manual labels to avoid LaTeX compilation if system lacks it
        for i in range(0, 13):
            # n2p = number_to_point
            point = number_line.n2p(i)
            label = Text(str(i), font_size=16).next_to(point, DOWN)
            self.add(label)

        # Visualize intervals
        interval_mobjects: List[VGroup] = []
        for i, (start, end) in enumerate(intervals):
            # Map start/end to position on number line
            p1 = number_line.n2p(start)
            p2 = number_line.n2p(end)

            # Create bar
            bar = Rectangle(
                width=p2[0] - p1[0], height=0.5, color=WHITE, fill_opacity=0.3
            )
            # Stagger height to show overlaps visually
            y_pos = 0 + (i % 3) * 0.7
            bar.move_to([(p1[0] + p2[0]) / 2, y_pos, 0])

            label = Text(f"({start},{end})", font_size=16).move_to(bar.get_center())

            group = VGroup(bar, label)
            interval_mobjects.append(group)
            self.play(FadeIn(group), run_time=0.3)

        self.wait(1)

        # Greedy Algorithm: Sort by end time
        # Note: In Python stable sort is guaranteed, but order doesn't strictly matter for logic here
        sorted_intervals = sorted(intervals, key=lambda x: x[1])

        # Re-arrange intervals to show sorting (conceptual)
        info_text = Text("Sorting by end time...", font_size=24, color=YELLOW)
        info_text.to_edge(LEFT)
        self.play(Write(info_text))
        self.wait(1)

        self.play(
            Transform(
                info_text,
                Text(
                    "Selecting non-overlapping...", font_size=24, color=GREEN
                ).to_edge(LEFT),
            )
        )

        selected_intervals: List[Tuple[int, int]] = []
        last_end_time = -1

        for i, (start, end) in enumerate(sorted_intervals):
            # Find the mobject corresponding to this interval
            # (In a real app, we'd map better, here we search by text label)
            target_mobj: Optional[VGroup] = None
            for mobj in interval_mobjects:
                # mobj is VGroup(Rectangle, Text)
                # Text mobject stores its content in .text or .original_text depending on manim version
                # Safest way often is checking the string constructed
                # But here we rely on exact string match if stored, or just re-construct logic
                # Let's try to match by position approx or just assume order if we hadn't shuffled mobjects
                # But we processed sorted_intervals which is different order.

                # Let's match by label text content
                text_obj = mobj[1]
                # Accessing text content in Manim can be tricky across versions.
                # Assuming `text` attribute exists for Text objects.
                if getattr(text_obj, "text", "") == f"({start},{end})":
                     # Handle duplicate intervals if any (none in this dataset)
                    target_mobj = mobj
                    break

            if not target_mobj:
                continue

            # Highlight current candidate
            self.play(target_mobj.animate.set_color(YELLOW), run_time=0.3)

            if start >= last_end_time:
                # Select
                self.play(
                    target_mobj.animate.set_color(GREEN).set_fill(opacity=0.8),
                    run_time=0.5,
                )
                selected_intervals.append((start, end))
                last_end_time = end
            else:
                # Reject
                self.play(
                    target_mobj.animate.set_color(RED).set_fill(opacity=0.1),
                    run_time=0.3,
                )

        self.wait(2)
