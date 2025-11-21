from manim import *
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

class TrieDemo(Scene):
    def construct(self):
        # Title
        title = Text("Trie (Prefix Tree) Visualization", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Words to insert
        words = ["cat", "car", "dog"]
        
        # Visual representation of nodes
        # We'll use a simplified manual layout for this demo
        
        root_pos = UP * 2
        root_node = Circle(radius=0.4, color=WHITE)
        root_label = Text("root", font_size=16).move_to(root_pos)
        root_node.move_to(root_pos)
        
        self.play(Create(root_node), Write(root_label))
        
        nodes = {"": (root_node, root_pos)}
        edges = []
        
        def get_pos(prefix):
            # Simple deterministic layout
            depth = len(prefix)
            if depth == 0: return root_pos
            
            # Calculate x based on hash/char to spread out
            # This is a hacky layout for demo purposes
            parent_pos = nodes[prefix[:-1]][1]
            
            # Determine child index
            char = prefix[-1]
            offset = (ord(char) - ord('a') - 12) * 0.5 # Spread -6 to +6
            
            # Adjust based on depth to avoid overlap
            x_spread = 4 / (depth)
            if prefix.startswith("c"):
                base_x = -2
            else:
                base_x = 2
                
            if len(prefix) > 1:
                if prefix[-1] == 't': x_offset = -1
                elif prefix[-1] == 'r': x_offset = 1
                elif prefix[-1] == 'g': x_offset = 0
                else: x_offset = 0
                new_x = parent_pos[0] + x_offset
            else:
                new_x = base_x
                
            return np.array([new_x, parent_pos[1] - 1.5, 0])

        for word in words:
            word_text = Text(f"Inserting: {word}", font_size=24, color=YELLOW)
            word_text.next_to(title, DOWN)
            self.play(FadeIn(word_text))
            
            curr_prefix = ""
            curr_node_mobj = nodes[""][0]
            
            for char in word:
                next_prefix = curr_prefix + char
                
                if next_prefix not in nodes:
                    # Create new node
                    pos = get_pos(next_prefix)
                    new_node = Circle(radius=0.3, color=BLUE)
                    new_node.move_to(pos)
                    label = Text(char, font_size=20).move_to(pos)
                    
                    # Create edge
                    edge = Line(curr_node_mobj.get_bottom(), new_node.get_top(), color=GREY)
                    
                    self.play(Create(edge), Create(new_node), Write(label), run_time=0.5)
                    
                    nodes[next_prefix] = (new_node, pos)
                    edges.append(edge)
                else:
                    # Highlight existing
                    new_node = nodes[next_prefix][0]
                    self.play(new_node.animate.set_fill(YELLOW, opacity=0.5), run_time=0.3)
                    self.play(new_node.animate.set_fill(opacity=0), run_time=0.3)
                
                curr_prefix = next_prefix
                curr_node_mobj = nodes[curr_prefix][0]
                
            # Mark end of word
            self.play(curr_node_mobj.animate.set_color(GREEN), run_time=0.5)
            self.play(FadeOut(word_text))
            
        self.wait(2)
