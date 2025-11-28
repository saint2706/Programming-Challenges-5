"""Visualization of Consistent Hashing using Manim.

This script demonstrates the placement of nodes on a hash ring and how keys
are mapped to the nearest node in clockwise direction.
"""

import os
import sys
from typing import Dict

import numpy as np
from manim import *  # type: ignore

# Add parent directory to path to import hash_ring
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Safe import
try:
    from hash_ring import HashRing
except ImportError:
    pass


class ConsistentHashingDemo(Scene):
    """Manim Scene for demonstrating Consistent Hashing."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("Consistent Hashing", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Draw Ring
        ring = Circle(radius=3, color=WHITE)
        self.play(Create(ring))

        # Helper to map hash to angle
        def hash_to_angle(h: int) -> float:
            """Map hash space to 0-2PI radians."""
            # SHA-256 max hash
            max_hash = 2**256
            # Normalize to [0, 1] then scale to [0, 2PI]
            # Note: Manim circles start at 0 degrees (Right) and go counter-clockwise.
            # Consistent hashing typically goes clockwise, but visual mapping holds.
            return (h / max_hash) * 2 * PI

        # Create Hash Ring instance
        hr = HashRing()
        nodes = ["Node A", "Node B", "Node C"]
        node_colors = {"Node A": RED, "Node B": GREEN, "Node C": BLUE}

        # Add nodes and visualize
        node_dots = VGroup()
        node_labels = VGroup()

        # Map node name to its Dot mobject for later reference
        node_dot_map: Dict[str, Dot] = {}

        for node in nodes:
            hr.add_node(node, vnode_count=1)  # Use 1 vnode for clarity

            # Get the hash of the node
            # Find the bucket corresponding to this node
            bucket = [b for b in hr.buckets if b.node == node][0]
            angle = hash_to_angle(bucket.hash)

            # Position on circle
            x = 3 * np.cos(angle)
            y = 3 * np.sin(angle)

            dot = Dot(point=[x, y, 0], color=node_colors[node])
            label = Text(node, font_size=20).next_to(dot, OUT)

            node_dots.add(dot)
            node_labels.add(label)
            node_dot_map[node] = dot

            self.play(FadeIn(dot), Write(label), run_time=0.5)

        self.wait(1)

        # Visualize Keys
        keys = ["Key 1", "Key 2", "Key 3", "Key 4"]

        for key in keys:
            # Calculate key hash
            key_hash = hr.hash_function(key)
            angle = hash_to_angle(key_hash)

            x = 3 * np.cos(angle)
            y = 3 * np.sin(angle)

            key_dot = Dot(point=[x, y, 0], color=YELLOW)
            key_label = Text(key, font_size=16).next_to(key_dot, IN)

            self.play(FadeIn(key_dot), Write(key_label), run_time=0.5)

            # Find mapped node
            mapped_node = hr.lookup(key)[0]

            # Draw line to mapped node
            target_dot = node_dot_map.get(mapped_node)

            if target_dot:
                line = DashedLine(
                    key_dot.get_center(), target_dot.get_center(), color=YELLOW
                )
                self.play(Create(line), run_time=0.5)
                self.wait(0.5)
                self.play(FadeOut(line))

        self.wait(2)
