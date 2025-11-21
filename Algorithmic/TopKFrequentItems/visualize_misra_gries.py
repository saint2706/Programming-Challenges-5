from manim import *
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from misra_gries import MisraGriesCounter

class MisraGriesDemo(Scene):
    def construct(self):
        # Title
        title = Text("Misra-Gries Heavy Hitters", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Parameters
        k = 3
        mg = MisraGriesCounter(k=k)
        
        # Stream of items
        stream = ["A", "B", "A", "C", "A", "B", "D", "E", "A", "C", "F", "A"]
        
        # Visual elements
        stream_text = Text("Stream: " + " ".join(stream), font_size=24)
        stream_text.next_to(title, DOWN)
        self.play(FadeIn(stream_text))
        
        # Counters display
        counters_group = VGroup()
        counters_group.move_to(ORIGIN)
        
        def update_display():
            new_group = VGroup()
            for i, (item, count) in enumerate(mg.counters.items()):
                box = Square(side_length=1.5, color=BLUE)
                label = Text(f"{item}\n{count}", font_size=36)
                label.move_to(box.get_center())
                item_group = VGroup(box, label)
                
                # Position
                item_group.shift(RIGHT * (i - (k-2)/2) * 2) 
                new_group.add(item_group)
            return new_group

        current_display = update_display()
        self.play(Create(current_display))
        
        # Process stream
        pointer = Arrow(start=UP, end=DOWN, color=YELLOW)
        
        for i, item in enumerate(stream):
            # Highlight current item in stream text (approximate position)
            # A better way would be to create individual Text objects for the stream
            # For now, we just show the item being processed
            
            processing_text = Text(f"Processing: {item}", font_size=24, color=YELLOW)
            processing_text.next_to(stream_text, DOWN)
            self.add(processing_text)
            
            mg.update(item)
            
            new_display = update_display()
            
            self.play(
                Transform(current_display, new_display),
                run_time=0.5
            )
            self.remove(processing_text)
            current_display = new_display
            
        self.wait(2)
