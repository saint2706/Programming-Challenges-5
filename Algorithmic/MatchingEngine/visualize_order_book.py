"""Visualization of Order Book Matching Engine using Manim.

Demonstrates price-time priority order matching.
"""

import os
import sys

from manim import *

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class OrderBookDemo(Scene):
    """Manim Scene for demonstrating Order Book Matching."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Order Book Matching Engine", font_size=32)
        title.to_edge(UP)
        self.play(Write(title))

        # Create bid/ask headers
        bid_header = Text("BIDS (Buy)", font_size=20, color=GREEN)
        bid_header.move_to(LEFT * 4 + UP * 2)
        ask_header = Text("ASKS (Sell)", font_size=20, color=RED)
        ask_header.move_to(RIGHT * 4 + UP * 2)

        self.play(Write(bid_header), Write(ask_header))

        # Column headers
        bid_cols = Text("Price  Qty", font_size=14, color=GRAY)
        bid_cols.next_to(bid_header, DOWN)
        ask_cols = Text("Price  Qty", font_size=14, color=GRAY)
        ask_cols.next_to(ask_header, DOWN)
        self.play(Write(bid_cols), Write(ask_cols))

        # Initial order book state
        bids = [(100.00, 50), (99.50, 30), (99.00, 100)]  # price, quantity
        asks = [(101.00, 40), (101.50, 60), (102.00, 80)]

        bid_rows = VGroup()
        ask_rows = VGroup()

        def create_order_row(price, qty, is_bid=True):
            color = GREEN if is_bid else RED
            text = Text(f"${price:.2f}  {qty}", font_size=16, color=color)
            return text

        # Display initial bids
        for i, (price, qty) in enumerate(bids):
            row = create_order_row(price, qty, is_bid=True)
            row.move_to(LEFT * 4 + UP * (1 - i * 0.5))
            bid_rows.add(row)
            self.play(Write(row), run_time=0.2)

        # Display initial asks
        for i, (price, qty) in enumerate(asks):
            row = create_order_row(price, qty, is_bid=False)
            row.move_to(RIGHT * 4 + UP * (1 - i * 0.5))
            ask_rows.add(row)
            self.play(Write(row), run_time=0.2)

        self.wait(0.5)

        # Spread indicator
        spread = Text(
            f"Spread: ${asks[0][0] - bids[0][0]:.2f}",
            font_size=18,
            color=YELLOW,
        )
        spread.move_to(DOWN * 0.5)
        self.play(Write(spread))
        self.wait(0.5)

        # Incoming market buy order
        order_info = Text("Incoming: Market BUY 70 shares", font_size=20, color=BLUE)
        order_info.to_edge(LEFT).shift(DOWN * 2)
        self.play(Write(order_info))

        incoming_qty = 70

        # Match against asks
        matches = VGroup()
        matched_text = Text("Matches:", font_size=16, color=WHITE)
        matched_text.next_to(order_info, DOWN, aligned_edge=LEFT)
        self.play(Write(matched_text))

        match_y = matched_text.get_center()[1] - 0.4

        remaining = incoming_qty
        ask_idx = 0

        while remaining > 0 and ask_idx < len(asks):
            price, qty = asks[ask_idx]

            # Highlight the ask being matched
            self.play(
                ask_rows[ask_idx].animate.set_color(YELLOW).scale(1.1),
                run_time=0.3,
            )

            fill_qty = min(remaining, qty)
            remaining -= fill_qty

            # Show match
            match_text = Text(
                f"Filled {fill_qty} @ ${price:.2f}",
                font_size=14,
                color=GREEN,
            )
            match_text.move_to(LEFT * 4 + DOWN * (2.5 + ask_idx * 0.4))
            matches.add(match_text)
            self.play(Write(match_text), run_time=0.3)

            if fill_qty == qty:
                # Order fully filled, remove from book
                self.play(FadeOut(ask_rows[ask_idx]), run_time=0.3)
                ask_idx += 1
            else:
                # Partial fill, update quantity
                new_qty = qty - fill_qty
                new_row = create_order_row(price, new_qty, is_bid=False)
                new_row.move_to(ask_rows[ask_idx].get_center())
                self.play(
                    Transform(ask_rows[ask_idx], new_row),
                    run_time=0.3,
                )
                asks[ask_idx] = (price, new_qty)

        # Show completion
        if remaining == 0:
            complete = Text("Order fully filled!", font_size=24, color=GREEN)
        else:
            complete = Text(f"Partial fill, {remaining} remaining", font_size=24, color=YELLOW)

        complete.to_edge(DOWN)
        self.play(Write(complete))

        self.wait(2)


if __name__ == "__main__":
    pass
