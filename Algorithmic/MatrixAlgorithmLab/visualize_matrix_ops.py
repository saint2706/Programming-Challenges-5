from manim import *
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

class MatrixOpsDemo(Scene):
    def construct(self):
        # Title
        title = Text("Matrix Multiplication", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Matrices
        A = [[1, 2], [3, 4]]
        B = [[2, 0], [1, 2]]
        
        # Mobjects
        matrix_a = Matrix(A).set_color(BLUE)
        matrix_b = Matrix(B).set_color(GREEN)
        
        matrix_a.shift(LEFT * 3)
        matrix_b.next_to(matrix_a, RIGHT, buff=1)
        
        times = MathTex("\\times").move_to((matrix_a.get_right() + matrix_b.get_left()) / 2)
        equals = MathTex("=").next_to(matrix_b, RIGHT, buff=0.5)
        
        self.play(Create(matrix_a), Create(matrix_b), Write(times), Write(equals))
        
        # Result Matrix placeholder
        C = [[0, 0], [0, 0]]
        matrix_c = Matrix(C).next_to(equals, RIGHT, buff=0.5)
        
        # We will fill this manually
        # Get the entries of C
        c_entries = matrix_c.get_entries()
        
        # Calculate and animate
        # C[0][0] = A[0][0]*B[0][0] + A[0][1]*B[1][0]
        # 1*2 + 2*1 = 4
        
        # Helper to highlight row/col
        def highlight_row_col(row_idx, col_idx):
            row = matrix_a.get_rows()[row_idx]
            col = matrix_b.get_columns()[col_idx]
            
            self.play(
                row.animate.set_color(YELLOW),
                col.animate.set_color(YELLOW),
                run_time=0.5
            )
            return row, col
            
        def unhighlight(row, col):
            self.play(
                row.animate.set_color(BLUE),
                col.animate.set_color(GREEN),
                run_time=0.5
            )

        # Calculation steps
        steps = [
            (0, 0, 1*2 + 2*1),
            (0, 1, 1*0 + 2*2),
            (1, 0, 3*2 + 4*1),
            (1, 1, 3*0 + 4*2)
        ]
        
        for i, j, val in steps:
            row, col = highlight_row_col(i, j)
            
            # Show calculation text
            calc_text = Text(f"C[{i},{j}] = {val}", font_size=24).next_to(matrix_c, DOWN, buff=1)
            self.play(Write(calc_text))
            
            # Update result cell
            idx = i * 2 + j
            new_entry = MathTex(str(val)).move_to(c_entries[idx].get_center())
            self.play(Transform(c_entries[idx], new_entry))
            
            self.play(FadeOut(calc_text))
            unhighlight(row, col)
            
        self.wait(2)
