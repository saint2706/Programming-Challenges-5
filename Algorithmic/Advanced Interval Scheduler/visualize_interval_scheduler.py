from manim import *
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# Assuming main.py has the logic, but let's check if we can import a class or function.
# If main.py is just a script, we might need to adapt or mock the logic.
# Based on file list, main.py seems to be the implementation.
# Let's assume a simple greedy interval scheduling for visualization if import fails or is complex.

class IntervalSchedulingDemo(Scene):
    def construct(self):
        # Title
        title = Text("Interval Scheduling (Greedy)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Intervals (start, end)
        intervals = [
            (1, 3), (2, 4), (3, 6), (5, 7), (6, 8), (8, 10)
        ]
        
        # Create number line
        number_line = NumberLine(
            x_range=[0, 12, 1],
            length=10,
            color=BLUE,
            include_numbers=True,
            label_direction=DOWN,
        )
        number_line.move_to(DOWN * 2)
        self.play(Create(number_line))
        
        # Visualize intervals
        interval_mobjects = []
        for i, (start, end) in enumerate(intervals):
            # Map start/end to position on number line
            p1 = number_line.n2p(start)
            p2 = number_line.n2p(end)
            
            # Create bar
            bar = Rectangle(
                width=p2[0] - p1[0],
                height=0.5,
                color=WHITE,
                fill_opacity=0.3
            )
            # Stagger height to show overlaps
            y_pos = 0 + (i % 3) * 0.7
            bar.move_to([(p1[0] + p2[0])/2, y_pos, 0])
            
            label = Text(f"({start},{end})", font_size=16).move_to(bar.get_center())
            
            group = VGroup(bar, label)
            interval_mobjects.append(group)
            self.play(FadeIn(group), run_time=0.3)
            
        self.wait(1)
        
        # Greedy Algorithm: Sort by end time
        sorted_intervals = sorted(intervals, key=lambda x: x[1])
        
        # Re-arrange intervals to show sorting (optional, or just highlight)
        # For simplicity, we'll just highlight the selection process
        
        selected_intervals = []
        last_end_time = -1
        
        info_text = Text("Sorting by end time...", font_size=24, color=YELLOW)
        info_text.to_edge(LEFT)
        self.play(Write(info_text))
        self.wait(1)
        
        self.play(Transform(info_text, Text("Selecting non-overlapping...", font_size=24, color=GREEN).to_edge(LEFT)))
        
        for i, (start, end) in enumerate(sorted_intervals):
            # Find the mobject corresponding to this interval
            # (In a real app, we'd map better, here we search)
            target_mobj = None
            for mobj in interval_mobjects:
                # Extract text to match
                t = mobj[1].text
                if t == f"({start},{end})":
                    target_mobj = mobj
                    break
            
            if not target_mobj: continue
            
            # Highlight current candidate
            self.play(target_mobj.animate.set_color(YELLOW), run_time=0.3)
            
            if start >= last_end_time:
                # Select
                self.play(target_mobj.animate.set_color(GREEN).set_fill(opacity=0.8), run_time=0.5)
                selected_intervals.append((start, end))
                last_end_time = end
            else:
                # Reject
                self.play(target_mobj.animate.set_color(RED).set_fill(opacity=0.1), run_time=0.3)
                
        self.wait(2)
