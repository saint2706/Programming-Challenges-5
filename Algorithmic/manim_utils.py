from manim import *

def create_array_mobject(array, cell_width=0.8, cell_height=0.8, color=BLUE):
    """Creates a VGroup representing an array."""
    squares = VGroup()
    labels = VGroup()
    for i, value in enumerate(array):
        square = Square(side_length=cell_width).set_stroke(color=color)
        label = Text(str(value), font_size=24)
        if i > 0:
            square.next_to(squares[-1], RIGHT, buff=0)
        
        label.move_to(square.get_center())
        squares.add(square)
        labels.add(label)
    
    return VGroup(squares, labels)

def highlight_cell(array_mobject, index, color=YELLOW, run_time=0.5):
    """Returns an animation to highlight a specific cell in the array."""
    squares = array_mobject[0]
    return squares[index].animate(run_time=run_time).set_fill(color, opacity=0.5)

def unhighlight_cell(array_mobject, index, run_time=0.5):
    """Returns an animation to unhighlight a specific cell."""
    squares = array_mobject[0]
    return squares[index].animate(run_time=run_time).set_fill(opacity=0)
