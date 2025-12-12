"""Visualization of SAT Solver (DPLL) using Manim.

Demonstrates the Davis-Putnam-Logemann-Loveland algorithm for solving SAT.
"""

import os
import sys

from manim import *

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class SATSolverDemo(Scene):
    """Manim Scene for demonstrating DPLL SAT solving."""

    def construct(self) -> None:
        """Construct the animation scene."""
        # Title
        title = Text("SAT Solver (DPLL Algorithm)", font_size=32)
        title.to_edge(UP)
        self.play(Write(title))

        # Example CNF formula: (A ∨ B) ∧ (¬A ∨ C) ∧ (¬B ∨ ¬C)
        formula_text = Text(
            "(A ∨ B) ∧ (¬A ∨ C) ∧ (¬B ∨ ¬C)", font_size=24, color=YELLOW
        )
        formula_text.next_to(title, DOWN)
        self.play(Write(formula_text))
        self.wait(0.5)

        # Create clause boxes
        clauses = [
            ["A", "B"],
            ["¬A", "C"],
            ["¬B", "¬C"],
        ]

        clause_groups = VGroup()
        for i, clause in enumerate(clauses):
            box = Rectangle(width=2.5, height=0.8, color=WHITE)
            text = Text(" ∨ ".join(clause), font_size=18)
            text.move_to(box.get_center())
            group = VGroup(box, text)
            group.move_to(LEFT * 4 + RIGHT * i * 3 + UP * 0.5)
            clause_groups.add(group)

        self.play(Create(clause_groups), run_time=1)
        self.wait(0.5)

        # Decision tree visualization
        tree_root = Dot(point=DOWN * 1, color=WHITE)
        root_label = Text("Start", font_size=14).next_to(tree_root, UP, buff=0.1)

        self.play(Create(tree_root), Write(root_label))

        # Step 1: Try A = True
        step1 = Text("Try A = True", font_size=20, color=GREEN)
        step1.to_edge(LEFT).shift(DOWN * 2)
        self.play(Write(step1))

        # Highlight clause 1 as satisfied
        self.play(clause_groups[0][0].animate.set_color(GREEN), run_time=0.3)

        # Highlight clause 2 - A is false here, so need C
        self.play(clause_groups[1][0].animate.set_color(YELLOW), run_time=0.3)

        # Unit propagation: C must be True
        prop1 = Text("Unit Prop: C = True", font_size=18, color=BLUE)
        prop1.next_to(step1, DOWN, aligned_edge=LEFT)
        self.play(Write(prop1))

        # Clause 2 satisfied
        self.play(clause_groups[1][0].animate.set_color(GREEN), run_time=0.3)

        # Check clause 3: ¬B ∨ ¬C, but C=True so need ¬B
        self.play(clause_groups[2][0].animate.set_color(YELLOW), run_time=0.3)

        prop2 = Text("Unit Prop: B = False", font_size=18, color=BLUE)
        prop2.next_to(prop1, DOWN, aligned_edge=LEFT)
        self.play(Write(prop2))

        # All clauses satisfied
        self.play(clause_groups[2][0].animate.set_color(GREEN), run_time=0.3)

        # Show solution
        solution = Text("Solution: A=T, B=F, C=T", font_size=24, color=GREEN)
        solution.to_edge(DOWN)
        self.play(Write(solution))

        # Highlight success
        success_box = SurroundingRectangle(solution, color=GREEN, buff=0.2)
        self.play(Create(success_box))

        self.wait(2)


if __name__ == "__main__":
    pass
