from manim import *
import sys
import os

# Add parent directory to path to import kd_tree
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from kd_tree import build_kd_tree, KDNode

class KDTreeConstruction(Scene):
    def construct(self):
        # Title
        title = Text("K-d Tree Construction", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Define points
        points = [
            (2, 3), (5, 4), (9, 6), (4, 7), (8, 1), (7, 2)
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
        def visualize_split(node, x_min, x_max, y_min, y_max, depth):
            if node is None:
                return

            axis = depth % 2
            point = node.point
            
            if axis == 0: # Vertical split (x-axis)
                start = axes.c2p(point[0], y_min)
                end = axes.c2p(point[0], y_max)
                line = Line(start, end, color=YELLOW)
                self.play(Create(line), run_time=0.5)
                
                visualize_split(node.left, x_min, point[0], y_min, y_max, depth + 1)
                visualize_split(node.right, point[0], x_max, y_min, y_max, depth + 1)
            else: # Horizontal split (y-axis)
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
