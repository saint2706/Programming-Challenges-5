from manim import *
import sys
import os
import hashlib

# Add parent directory to path to import hash_ring
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from hash_ring import HashRing

class ConsistentHashingDemo(Scene):
    def construct(self):
        # Title
        title = Text("Consistent Hashing", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        # Draw Ring
        ring = Circle(radius=3, color=WHITE)
        self.play(Create(ring))
        
        # Helper to map hash to angle
        def hash_to_angle(h):
            # Map 0-2^256 to 0-360 degrees (0-2PI radians)
            # For visualization, we'll just use a simpler mapping or mock it
            # Since the real hash is huge, we normalize it.
            max_hash = 2**256
            return (h / max_hash) * 2 * PI

        # Create Hash Ring instance
        hr = HashRing()
        nodes = ["Node A", "Node B", "Node C"]
        node_colors = {"Node A": RED, "Node B": GREEN, "Node C": BLUE}
        
        # Add nodes and visualize
        node_dots = VGroup()
        node_labels = VGroup()
        
        for node in nodes:
            hr.add_node(node, vnode_count=1) # Use 1 vnode for clarity
            
            # Get the hash of the node (we access private member for viz)
            # In the real class, buckets are sorted.
            # We find the bucket corresponding to this node.
            bucket = [b for b in hr.buckets if b.node == node][0]
            angle = hash_to_angle(bucket.hash)
            
            # Position on circle
            x = 3 * np.cos(angle)
            y = 3 * np.sin(angle)
            
            dot = Dot(point=[x, y, 0], color=node_colors[node])
            label = Text(node, font_size=20).next_to(dot, OUT)
            
            node_dots.add(dot)
            node_labels.add(label)
            
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
            # We need to find the dot corresponding to the mapped node
            target_dot = None
            for i, n in enumerate(nodes):
                if n == mapped_node:
                    target_dot = node_dots[i]
                    break
            
            if target_dot:
                line = DashedLine(key_dot.get_center(), target_dot.get_center(), color=YELLOW)
                self.play(Create(line), run_time=0.5)
                self.wait(0.5)
                self.play(FadeOut(line))

        self.wait(2)
