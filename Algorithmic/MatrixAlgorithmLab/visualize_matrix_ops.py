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
        
        def create_matrix_mob(matrix, color=WHITE):
            rows = len(matrix)
            cols = len(matrix[0])
            group = VGroup()
            
            # Brackets
            height = rows * 0.8
            width = cols * 0.8
            
            left_bracket = Text("[", font_size=48).scale_to_fit_height(height)
            right_bracket = Text("]", font_size=48).scale_to_fit_height(height)
            
            left_bracket.move_to(LEFT * (width/2 + 0.2))
            right_bracket.move_to(RIGHT * (width/2 + 0.2))
            
            group.add(left_bracket, right_bracket)
            
            # Entries
            entries = VGroup()
            for i in range(rows):
                for j in range(cols):
                    entry = Text(str(matrix[i][j]), font_size=24, color=color)
                    # Position
                    x = (j - (cols-1)/2) * 0.8
                    y = ((rows-1)/2 - i) * 0.8
                    entry.move_to([x, y, 0])
                    entries.add(entry)
            
            group.add(entries)
            return group, entries

        # Mobjects
        matrix_a_group, entries_a = create_matrix_mob(A, BLUE)
        matrix_b_group, entries_b = create_matrix_mob(B, GREEN)
        
        matrix_a_group.shift(LEFT * 3)
        matrix_b_group.next_to(matrix_a_group, RIGHT, buff=1)
        
        times = Text("x", font_size=36).move_to((matrix_a_group.get_right() + matrix_b_group.get_left()) / 2)
        equals = Text("=", font_size=36).next_to(matrix_b_group, RIGHT, buff=0.5)
        
        self.play(Create(matrix_a_group), Create(matrix_b_group), Write(times), Write(equals))
        
        # Result Matrix placeholder
        C = [[0, 0], [0, 0]]
        matrix_c_group, entries_c = create_matrix_mob(C, WHITE)
        matrix_c_group.next_to(equals, RIGHT, buff=0.5)
        
        self.play(Create(matrix_c_group))
        
        # Helper to highlight row/col
        def highlight_row_col(row_idx, col_idx):
            # Get row entries from A
            row_entries = VGroup()
            for j in range(len(A[0])):
                idx = row_idx * len(A[0]) + j
                row_entries.add(entries_a[idx])
                
            # Get col entries from B
            col_entries = VGroup()
            for i in range(len(B)):
                idx = i * len(B[0]) + col_idx
                col_entries.add(entries_b[idx])
            
            self.play(
                row_entries.animate.set_color(YELLOW),
                col_entries.animate.set_color(YELLOW),
                run_time=0.5
            )
            return row_entries, col_entries
            
        def unhighlight(row_entries, col_entries):
            self.play(
                row_entries.animate.set_color(BLUE),
                col_entries.animate.set_color(GREEN),
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
            calc_text = Text(f"C[{i},{j}] = {val}", font_size=24).next_to(matrix_c_group, DOWN, buff=1)
            self.play(Write(calc_text))
            
            # Update result cell
            idx = i * 2 + j
            new_entry = Text(str(val), font_size=24).move_to(entries_c[idx].get_center())
            self.play(Transform(entries_c[idx], new_entry))
            
            self.play(FadeOut(calc_text))
            unhighlight(row, col)
            
        self.wait(2)
