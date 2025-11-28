"""
Implementation of the algorithm.
"""

from dynamic_connectivity import DynamicConnectivity

def main():
    """
    Docstring for main.
    """
    dc = DynamicConnectivity()

    print("Adding edges: (A, B), (B, C), (C, D), (D, E)")
    dc.add_edge('A', 'B')
    dc.add_edge('B', 'C')
    dc.add_edge('C', 'D')
    dc.add_edge('D', 'E')

    print(f"Connected A-E? {dc.connected('A', 'E')}") # True

    print("Adding redundant edge (A, E) (creates cycle)")
    dc.add_edge('A', 'E')

    print("Removing critical edge (C, D)")
    dc.remove_edge('C', 'D')

    # Structure should use (A, E) to reconnect the components {A, B, C} and {D, E} (via E->A->B->C)
    # Wait, A-E connects {A,B,C,E,D} if path exists.
    # Spanning tree before remove: A-B-C-D-E
    # Remove C-D. Trees: {A,B,C} and {D,E}.
    # Replacement edge search:
    # Scan {D,E}. E has edge to A. A is not in {D,E}.
    # Add (A, E) to spanning tree.
    # Connected!

    print(f"Connected A-E? {dc.connected('A', 'E')}")
    print(f"Connected B-D? {dc.connected('B', 'D')}")

    print("Removing (A, E)")
    dc.remove_edge('A', 'E')

    print(f"Connected A-E? {dc.connected('A', 'E')}") # Should be False now

if __name__ == "__main__":
    main()
