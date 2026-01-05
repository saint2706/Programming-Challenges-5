"""Visualization of Misra-Gries Algorithm using Manim.

This script demonstrates the Misra-Gries heavy hitter algorithm processing a stream
of items and maintaining a limited set of counters.
"""

import os
import sys

from manim import *  # type: ignore

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Safe import for execution in diverse environments
try:
    from misra_gries import MisraGriesCounter
except ImportError:
    # Fallback if module cannot be imported directly (e.g. manim execution context)
    pass


class MisraGriesDemo(Scene):
    """Manim Scene for demonstrating Misra-Gries algorithm."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Misra-Gries Heavy Hitters", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Parameters
        k = 3
        # Assume MisraGriesCounter is available or mock it for pure viz if needed
        # In a real run, the import above works.
        mg = MisraGriesCounter(k=k)

        # Stream of items
        stream = ["A", "B", "A", "C", "A", "B", "D", "E", "A", "C", "F", "A"]

        # Visual elements
        stream_text = Text("Stream: " + " ".join(stream), font_size=24)
        stream_text.next_to(title, DOWN)
        self.play(FadeIn(stream_text))

        # Counters display
        # We maintain a reference to the VGroup currently on screen to transform it
        current_display = VGroup()
        current_display.move_to(ORIGIN)

        def update_display() -> VGroup:
            """Create a new VGroup representing the current state of counters."""
            new_group = VGroup()
            # Sort keys for stable visualization
            # Use approximate_counts() to get corrected values if optimized
            sorted_items = sorted(mg.approximate_counts().items())

            count_items = len(sorted_items)
            if count_items == 0:
                return new_group

            for i, (item, count) in enumerate(sorted_items):
                box = Square(side_length=1.5, color=BLUE)
                label = Text(f"{item}\n{count}", font_size=36)
                label.move_to(box.get_center())
                item_group = VGroup(box, label)

                # Position
                # Center the group of boxes
                x_offset = (i - (count_items - 1) / 2) * 2
                item_group.move_to(RIGHT * x_offset)
                new_group.add(item_group)
            return new_group

        # Initial empty display
        self.play(Create(current_display))

        # Process stream
        for i, item in enumerate(stream):
            processing_text = Text(f"Processing: {item}", font_size=24, color=YELLOW)
            processing_text.next_to(stream_text, DOWN)
            self.add(processing_text)

            mg.update(item)

            new_display = update_display()

            # Transform current counters to new state
            if len(current_display) == 0 and len(new_display) > 0:
                self.play(FadeIn(new_display), run_time=0.5)
            elif len(new_display) == 0 and len(current_display) > 0:
                self.play(FadeOut(current_display), run_time=0.5)
            else:
                self.play(Transform(current_display, new_display), run_time=0.5)

            # Update reference
            current_display = new_display
            self.remove(processing_text)

        self.wait(2)
