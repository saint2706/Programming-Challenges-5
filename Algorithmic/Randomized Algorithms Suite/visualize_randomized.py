"""Visualization of Randomized Data Structures (Skip List) using Manim.

This script demonstrates the structure and search operation of a Skip List.
"""

import sys
import os
from typing import List, Dict, Any, Tuple

from manim import *  # type: ignore

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class SkipListDemo(Scene):
    """Manim Scene for demonstrating Skip List structure and search."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Skip List Visualization", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Skip List Structure
        # We'll simulate a small skip list
        # Level 3: -inf ---------------------> inf
        # Level 2: -inf --------> 5 ---------> inf
        # Level 1: -inf -> 3 ---> 5 ---> 8 --> inf
        # Level 0: -inf -> 3 -> 4 -> 5 -> 8 -> 9 -> inf

        levels = 4
        # data map not strictly needed for drawing, but good for logic if we built it dynamically
        # data = {
        #     3: [0, 1, 2, 3],
        #     2: [0, 1, 2],
        #     1: [0, 1],
        #     0: [0]
        # }

        # Nodes configuration
        nodes = [
            {"val": "-inf", "levels": 4, "pos": 0},
            {"val": 3, "levels": 2, "pos": 2},
            {"val": 4, "levels": 1, "pos": 3},
            {"val": 5, "levels": 3, "pos": 4},
            {"val": 8, "levels": 2, "pos": 6},
            {"val": 9, "levels": 1, "pos": 7},
            {"val": "inf", "levels": 4, "pos": 9},
        ]

        # Draw nodes
        # Key: (val, level) -> mobject group
        node_mobjects: Dict[Tuple[Any, int], VGroup] = {}

        start_x = -5
        start_y = -2
        x_step = 1.2
        y_step = 1.0

        for node in nodes:
            val = node["val"]
            max_level = node["levels"]
            x_pos = start_x + node["pos"] * x_step

            for lvl in range(max_level):
                y_pos = start_y + lvl * y_step

                box = Square(side_length=0.6, color=BLUE)
                box.move_to([x_pos, y_pos, 0])

                label = Text(str(val), font_size=16).move_to(box.get_center())

                group = VGroup(box, label)
                node_mobjects[(val, lvl)] = group
                self.add(group)

        # Draw arrows
        arrows: List[Arrow] = []

        # Horizontal arrows
        for lvl in range(levels):
            current_node = nodes[0]
            for next_node in nodes[1:]:
                if next_node["levels"] > lvl:
                    # Draw arrow from current to next
                    start = node_mobjects[
                        (current_node["val"], lvl)
                    ].get_right()
                    end = node_mobjects[(next_node["val"], lvl)].get_left()
                    arrow = Arrow(
                        start,
                        end,
                        buff=0.1,
                        max_tip_length_to_length_ratio=0.15,
                    )
                    self.add(arrow)
                    arrows.append(arrow)
                    current_node = next_node

        self.wait(1)

        # Search for 8
        target = 8
        search_text = Text(
            f"Searching for {target}", font_size=24, color=YELLOW
        )
        search_text.next_to(title, DOWN)
        self.play(FadeIn(search_text))

        curr_val = "-inf"
        curr_lvl = levels - 1

        pointer = Arrow(start=UP, end=DOWN, color=RED).next_to(
            node_mobjects[(curr_val, curr_lvl)], UP
        )
        self.play(Create(pointer))

        # path = [] # Unused

        while curr_lvl >= 0:
            # Highlight current
            curr_mobj = node_mobjects[(curr_val, curr_lvl)]
            self.play(
                curr_mobj[0].animate.set_fill(YELLOW, opacity=0.5),
                run_time=0.3,
            )
            # path.append(curr_mobj)

            # Helper for comparison
            def is_greater(a: Any, b: Any) -> bool:
                """
                Docstring for is_greater.
                """
                if a == "inf":
                    return True
                if b == "inf":
                    return False
                if a == "-inf":
                    return False
                if b == "-inf":
                    return True
                return a > b

            # Find next node at this level
            next_node = None
            for n in nodes:
                if n["val"] == curr_val:
                    continue

                # Check if node exists at this level
                if n["levels"] > curr_lvl:
                    # Check if it's greater than current
                    if is_greater(n["val"], curr_val):
                        if next_node is None:
                            next_node = n
                        elif is_greater(next_node["val"], n["val"]):
                            next_node = n
            
            # Logic for moving pointer
            if next_node is None:
                 # Should not happen with inf sentinel
                 break

            if next_node["val"] == "inf" or is_greater(
                next_node["val"], target
            ):
                # Go down
                if curr_lvl > 0:
                    self.play(
                        pointer.animate.next_to(
                            node_mobjects[(curr_val, curr_lvl - 1)], UP
                        ),
                        run_time=0.3,
                    )
                curr_lvl -= 1
            elif next_node["val"] == target:
                # Found!
                self.play(
                    pointer.animate.next_to(
                        node_mobjects[(target, curr_lvl)], UP
                    ),
                    run_time=0.5,
                )
                found_mobj = node_mobjects[(target, curr_lvl)]
                self.play(
                    found_mobj[0].animate.set_fill(GREEN, opacity=0.8),
                    run_time=0.5,
                )
                break
            else:
                # Go right
                curr_val = next_node["val"]
                self.play(
                    pointer.animate.next_to(
                        node_mobjects[(curr_val, curr_lvl)], UP
                    ),
                    run_time=0.3,
                )

        self.wait(2)
