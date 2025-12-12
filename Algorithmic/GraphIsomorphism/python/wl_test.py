"""Graph Isomorphism Checker (Heuristic).

Uses Weisfeiler-Lehman (WL) Color Refinement algorithm.
"""

import hashlib
from typing import List


def get_graph_hash(adj: List[List[int]], iterations: int = 3) -> str:
    """Compute WL hash for a graph.

    Args:
        adj: Adjacency list (0-indexed).
        iterations: Number of refinement steps.
    """
    n = len(adj)
    # Initial colors (degrees)
    colors = [str(len(adj[i])) for i in range(n)]

    for _ in range(iterations):
        new_colors = []
        for i in range(n):
            # Collect neighbor colors
            neighbor_colors = sorted([colors[neighbor] for neighbor in adj[i]])
            # Hash (current_color + neighbors)
            s = colors[i] + "(" + "".join(neighbor_colors) + ")"
            new_colors.append(hashlib.sha256(s.encode()).hexdigest())
        colors = new_colors

    # Canonical label is sorted colors
    canonical = sorted(colors)
    return hashlib.sha256("".join(canonical).encode()).hexdigest()


def are_isomorphic(adj1: List[List[int]], adj2: List[List[int]]) -> bool:
    """Check if two graphs are likely isomorphic."""
    if len(adj1) != len(adj2):
        return False
    # Check edges count
    edges1 = sum(len(x) for x in adj1)
    edges2 = sum(len(x) for x in adj2)
    if edges1 != edges2:
        return False

    h1 = get_graph_hash(adj1)
    h2 = get_graph_hash(adj2)
    return h1 == h2
