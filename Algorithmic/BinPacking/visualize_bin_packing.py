"""Visualization of Bin Packing Algorithm using Manim.

Demonstrates the First Fit Decreasing (FFD) bin packing heuristic.
"""

import os
import sys

from manim import *

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class BinPackingDemo(Scene):
    """Manim Scene for demonstrating Bin Packing with First Fit Decreasing."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Bin Packing (First Fit Decreasing)", font_size=32)
        title.to_edge(UP)
        self.play(Write(title))

        # Items with sizes (will be sorted descending)
        items = [4, 8, 5, 1, 7, 6, 1, 4, 2, 2]
        bin_capacity = 10

        # Sort items in decreasing order (FFD)
        sorted_items = sorted(items, reverse=True)

        # Show items
        info = Text(f"Items: {items}", font_size=20)
        info.next_to(title, DOWN)
        self.play(Write(info))
        self.wait(0.5)

        sorted_info = Text(f"Sorted (desc): {sorted_items}", font_size=20, color=YELLOW)
        sorted_info.next_to(info, DOWN)
        self.play(Write(sorted_info))
        self.wait(0.5)

        # Bins visualization area
        bins_group = VGroup()
        bin_contents = []  # Track current fill level of each bin
        bin_rects = []

        def create_bin(index):
            """Create a bin rectangle."""
            bin_rect = Rectangle(width=1.2, height=3, color=BLUE)
            bin_rect.move_to(LEFT * 4 + RIGHT * index * 1.5 + DOWN * 0.5)
            label = Text(f"B{index + 1}", font_size=14).next_to(bin_rect, DOWN)
            cap_label = Text(f"0/{bin_capacity}", font_size=12).next_to(bin_rect, UP)
            return VGroup(bin_rect, label, cap_label)

        # Process each item
        for item_idx, item_size in enumerate(sorted_items):
            # Show current item
            item_text = Text(f"Item: {item_size}", font_size=24, color=GREEN)
            item_text.to_edge(RIGHT).shift(UP)
            self.play(Write(item_text), run_time=0.3)

            # Find first bin that fits
            placed = False
            for bin_idx in range(len(bin_contents)):
                if bin_contents[bin_idx] + item_size <= bin_capacity:
                    # Fits! Add to this bin
                    bin_contents[bin_idx] += item_size

                    # Animate adding item to bin
                    bin_group = bins_group[bin_idx]
                    bin_rect = bin_group[0]

                    # Create item block
                    fill_height = (item_size / bin_capacity) * 3
                    item_block = Rectangle(
                        width=1.0,
                        height=fill_height,
                        color=GREEN,
                        fill_opacity=0.7,
                    )

                    # Position in bin
                    current_fill = sum(
                        [
                            child.height
                            for child in bin_group
                            if isinstance(child, Rectangle) and child.color == GREEN
                        ]
                    )
                    base_y = bin_rect.get_bottom()[1] + current_fill + fill_height / 2
                    item_block.move_to([bin_rect.get_center()[0], base_y, 0])

                    # Update capacity label
                    new_cap = Text(
                        f"{bin_contents[bin_idx]}/{bin_capacity}", font_size=12
                    )
                    new_cap.next_to(bin_rect, UP)

                    self.play(
                        FadeIn(item_block),
                        Transform(bin_group[2], new_cap),
                        run_time=0.4,
                    )
                    bin_group.add(item_block)

                    placed = True
                    break

            if not placed:
                # Create new bin
                new_bin = create_bin(len(bin_contents))
                bin_contents.append(item_size)
                bin_rects.append(new_bin)
                bins_group.add(new_bin)

                self.play(Create(new_bin), run_time=0.3)

                # Add item to new bin
                bin_rect = new_bin[0]
                fill_height = (item_size / bin_capacity) * 3
                item_block = Rectangle(
                    width=1.0,
                    height=fill_height,
                    color=GREEN,
                    fill_opacity=0.7,
                )
                base_y = bin_rect.get_bottom()[1] + fill_height / 2
                item_block.move_to([bin_rect.get_center()[0], base_y, 0])

                new_cap = Text(f"{item_size}/{bin_capacity}", font_size=12)
                new_cap.next_to(bin_rect, UP)

                self.play(
                    FadeIn(item_block),
                    Transform(new_bin[2], new_cap),
                    run_time=0.4,
                )
                new_bin.add(item_block)

            self.play(FadeOut(item_text), run_time=0.2)

        # Final result
        result = Text(f"Used {len(bin_contents)} bins", font_size=28, color=YELLOW)
        result.to_edge(DOWN)
        self.play(Write(result))
        self.wait(2)


if __name__ == "__main__":
    # For command line rendering
    pass
