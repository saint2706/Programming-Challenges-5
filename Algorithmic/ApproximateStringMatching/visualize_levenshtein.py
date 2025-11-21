from manim import *
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

class LevenshteinDemo(Scene):
    def construct(self):
        # Title
        title = Text("Levenshtein Distance (DP)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Strings
        s1 = "kitten"
        s2 = "sitting"
        
        # Matrix dimensions
        rows = len(s1) + 1
        cols = len(s2) + 1
        
        # Create grid
        grid = VGroup()
        cells = [[None for _ in range(cols)] for _ in range(rows)]
        
        cell_size = 0.8
        start_pos = UP * 2 + LEFT * 3
        
        # Headers
        for j, char in enumerate(" " + s2):
            label = Text(char, font_size=24)
            label.move_to(start_pos + RIGHT * (j + 1) * cell_size + UP * cell_size)
            self.add(label)
            
        for i, char in enumerate(" " + s1):
            label = Text(char, font_size=24)
            label.move_to(start_pos + DOWN * (i + 1) * cell_size + LEFT * cell_size)
            self.add(label)

        # Initialize grid cells
        for i in range(rows):
            for j in range(cols):
                square = Square(side_length=cell_size).set_stroke(color=WHITE)
                square.move_to(start_pos + RIGHT * (j + 1) * cell_size + DOWN * (i + 1) * cell_size)
                grid.add(square)
                cells[i][j] = {"square": square, "val": 0, "text": None}

        self.play(Create(grid))
        
        # DP Logic and Visualization
        dp = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # Initialize first row/col
        for i in range(rows):
            dp[i][0] = i
        for j in range(cols):
            dp[0][j] = j
            
        # Fill matrix
        for i in range(rows):
            for j in range(cols):
                if i == 0 and j == 0:
                    val = 0
                elif i == 0:
                    val = j
                elif j == 0:
                    val = i
                else:
                    if s1[i-1] == s2[j-1]:
                        val = dp[i-1][j-1]
                    else:
                        val = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                
                dp[i][j] = val
                
                # Animate filling
                text = Text(str(val), font_size=20)
                text.move_to(cells[i][j]["square"].get_center())
                cells[i][j]["text"] = text
                
                # Highlight current cell
                self.play(cells[i][j]["square"].animate.set_fill(YELLOW, opacity=0.5), run_time=0.1)
                self.add(text)
                self.play(cells[i][j]["square"].animate.set_fill(opacity=0), run_time=0.1)
                
        self.wait(1)
        
        # Show path (backtrack)
        i, j = rows - 1, cols - 1
        path_group = VGroup()
        
        while i > 0 or j > 0:
            rect = cells[i][j]["square"]
            self.play(rect.animate.set_stroke(color=RED, width=4), run_time=0.2)
            
            if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                # Substitution
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                # Deletion
                i -= 1
            else:
                # Insertion
                j -= 1
                
        # Highlight start
        self.play(cells[0][0]["square"].animate.set_stroke(color=RED, width=4))
        
        self.wait(2)
