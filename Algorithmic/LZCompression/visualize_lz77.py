"""Visualization of LZ77 Compression using Manim.

Demonstrates the sliding window compression algorithm.
"""

import os
import sys

from manim import *

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class LZ77CompressionDemo(Scene):
    """Manim Scene for demonstrating LZ77 compression."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("LZ77 Compression", font_size=32)
        title.to_edge(UP)
        self.play(Write(title))

        # Input string
        input_str = "AABCBBABC"
        window_size = 6

        # Create character boxes
        char_boxes = VGroup()
        for i, char in enumerate(input_str):
            box = Square(side_length=0.6)
            text = Text(char, font_size=20)
            text.move_to(box.get_center())
            group = VGroup(box, text)
            group.move_to(LEFT * 4 + RIGHT * i * 0.65)
            char_boxes.add(group)

        # Index labels
        idx_labels = VGroup()
        for i in range(len(input_str)):
            label = Text(str(i), font_size=12, color=GRAY)
            label.next_to(char_boxes[i], DOWN, buff=0.1)
            idx_labels.add(label)

        self.play(Create(char_boxes), Write(idx_labels), run_time=1)
        self.wait(0.5)

        # Window visualization
        window_rect = Rectangle(
            width=window_size * 0.65, height=0.8, color=BLUE, fill_opacity=0.1
        )
        lookahead_rect = Rectangle(
            width=3 * 0.65, height=0.8, color=GREEN, fill_opacity=0.1
        )

        legend = VGroup(
            Rectangle(width=0.3, height=0.3, color=BLUE, fill_opacity=0.3),
            Text("Search Buffer", font_size=14),
            Rectangle(width=0.3, height=0.3, color=GREEN, fill_opacity=0.3),
            Text("Lookahead", font_size=14),
        ).arrange(RIGHT, buff=0.2)
        legend.to_edge(RIGHT).shift(UP * 2)
        self.play(Create(legend))

        # Output tokens
        output_label = Text("Output:", font_size=20, color=YELLOW)
        output_label.to_edge(LEFT).shift(DOWN * 2)
        self.play(Write(output_label))

        tokens = VGroup()
        token_pos = output_label.get_right() + RIGHT * 0.5

        # Simulate LZ77
        pos = 0
        while pos < len(input_str):
            # Update window position
            window_start = max(0, pos - window_size)
            window_rect.move_to(
                char_boxes[window_start].get_center()
                + RIGHT * (min(pos, window_size) - 1) * 0.65 / 2
            )
            window_rect.set_width((pos - window_start) * 0.65 + 0.1)

            lookahead_end = min(pos + 3, len(input_str))
            lookahead_rect.move_to(
                char_boxes[pos].get_center()
                + RIGHT * (lookahead_end - pos - 1) * 0.65 / 2
            )
            lookahead_rect.set_width((lookahead_end - pos) * 0.65)

            self.play(
                char_boxes[pos][0].animate.set_color(YELLOW),
                Create(window_rect) if pos == 0 else window_rect.animate,
                Create(lookahead_rect) if pos == 0 else lookahead_rect.animate,
                run_time=0.3,
            )

            # Find longest match in search buffer
            best_offset = 0
            best_length = 0
            search_buffer = input_str[window_start:pos]
            lookahead = input_str[pos:lookahead_end]

            for offset in range(1, len(search_buffer) + 1):
                match_start = pos - offset
                length = 0
                while (
                    length < len(lookahead)
                    and pos + length < len(input_str)
                    and input_str[match_start + (length % offset)]
                    == input_str[pos + length]
                ):
                    length += 1
                if length > best_length:
                    best_length = length
                    best_offset = offset

            # Create token
            if best_length > 0:
                next_char = (
                    input_str[pos + best_length]
                    if pos + best_length < len(input_str)
                    else ""
                )
                token_text = f"({best_offset},{best_length},{next_char})"

                # Highlight match
                for i in range(best_length):
                    self.play(
                        char_boxes[pos + i][0].animate.set_color(GREEN),
                        run_time=0.15,
                    )

                pos += best_length + 1
            else:
                next_char = input_str[pos]
                token_text = f"(0,0,{next_char})"
                pos += 1

            # Add token to output
            token = Text(token_text, font_size=16, color=GREEN)
            token.move_to(token_pos)
            tokens.add(token)
            self.play(Write(token), run_time=0.3)
            token_pos += RIGHT * (len(token_text) * 0.12 + 0.3)

            self.wait(0.2)

        # Final result
        result = Text("Compression complete!", font_size=24, color=GREEN)
        result.to_edge(DOWN)
        self.play(Write(result))

        self.wait(2)


if __name__ == "__main__":
    pass
