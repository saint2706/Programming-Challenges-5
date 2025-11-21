"""Visualization of Bloom Filter operations using Manim.

This script generates an animation demonstrating how items are added to a Bloom Filter
and how membership checks are performed, highlighting the probabilistic nature of the structure.
"""

import sys
import os
import hashlib
from typing import List

from manim import *  # type: ignore

# Add parent directory to path to allow importing manim_utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from manim_utils import create_array_mobject, highlight_cell, unhighlight_cell
except ImportError:
    # Fallback if running from a different context or if manim_utils is missing
    print("Warning: manim_utils module not found. Visualization might fail.")


class BloomFilterDemo(Scene):
    """Manim Scene for demonstrating Bloom Filter operations."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Bloom Filter Visualization", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Parameters
        size = 10
        num_hashes = 3
        bit_array = [0] * size

        # Create array visualization
        # Note: create_array_mobject is expected to return a VGroup or similar Mobject
        array_mobj = create_array_mobject(bit_array, cell_width=0.6, cell_height=0.6)
        array_mobj.move_to(ORIGIN)
        self.play(Create(array_mobj))

        # Helper to mock hash functions
        def get_hashes(item: str) -> List[int]:
            """Generate deterministic pseudo-random hashes for visualization.

            Args:
                item: The string item to hash.

            Returns:
                List[int]: A list of 3 hash values (indices).
            """
            h1 = sum(ord(c) for c in item) % size
            h2 = (h1 * 3 + 7) % size
            h3 = (h1 * 7 + 11) % size
            return [h1, h2, h3]

        # Add items
        items_to_add = ["apple", "banana"]

        for item in items_to_add:
            item_text = Text(f"Adding: {item}", font_size=24, color=YELLOW)
            item_text.next_to(array_mobj, UP, buff=1)
            self.play(FadeIn(item_text))

            hashes = get_hashes(item)

            # Show hashing
            hash_text = Text(f"Hashes: {hashes}", font_size=20)
            hash_text.next_to(item_text, DOWN)
            self.play(Write(hash_text))

            # Animate setting bits
            anims = []
            for h in hashes:
                bit_array[h] = 1
                # Update label
                # Assuming array_mobj structure from manim_utils: [0] is grid, [1] is labels
                label = array_mobj[1][h]
                new_label = Text("1", font_size=24).move_to(label.get_center())
                anims.append(Transform(label, new_label))
                anims.append(highlight_cell(array_mobj, h, color=GREEN))

            self.play(*anims)
            self.wait(0.5)

            # Cleanup highlight
            anims = []
            for h in hashes:
                anims.append(unhighlight_cell(array_mobj, h))
            self.play(*anims)

            self.play(FadeOut(item_text), FadeOut(hash_text))

        self.wait(1)

        # Check items
        items_to_check = ["apple", "cherry"]

        for item in items_to_check:
            item_text = Text(f"Checking: {item}", font_size=24, color=BLUE)
            item_text.next_to(array_mobj, UP, buff=1)
            self.play(FadeIn(item_text))

            hashes = get_hashes(item)
            hash_text = Text(f"Hashes: {hashes}", font_size=20)
            hash_text.next_to(item_text, DOWN)
            self.play(Write(hash_text))

            # Check bits
            all_set = True
            anims = []
            for h in hashes:
                if bit_array[h] == 1:
                    anims.append(highlight_cell(array_mobj, h, color=GREEN))
                else:
                    anims.append(highlight_cell(array_mobj, h, color=RED))
                    all_set = False

            self.play(*anims)
            self.wait(0.5)

            result_text = "Possibly in set" if all_set else "Definitely not in set"
            result_color = GREEN if all_set else RED
            result = Text(result_text, font_size=24, color=result_color)
            result.next_to(array_mobj, DOWN, buff=1)
            self.play(Write(result))
            self.wait(1)

            # Cleanup
            anims = []
            for h in hashes:
                anims.append(unhighlight_cell(array_mobj, h))
            self.play(*anims, FadeOut(result), FadeOut(item_text), FadeOut(hash_text))

        self.wait(2)
