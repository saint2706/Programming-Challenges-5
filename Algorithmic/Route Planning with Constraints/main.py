"""
Implementation of the algorithm.
"""

from route_planner import Graph, RoutePlanner

def main():
    """
    Docstring for main.
    """
    g = Graph()
    # Create a grid-like graph
    # A -- B -- C
    # |    |    |
    # D -- E -- F
    # |    |    |
    # G -- H -- I

    edges = [
        ('A', 'B', 1), ('B', 'C', 1),
        ('D', 'E', 1), ('E', 'F', 1),
        ('G', 'H', 1), ('H', 'I', 1),
        ('A', 'D', 1), ('D', 'G', 1),
        ('B', 'E', 1), ('E', 'H', 1),
        ('C', 'F', 1), ('F', 'I', 1)
    ]

    for u, v, w in edges:
        g.add_edge(u, v, w)

    planner = RoutePlanner(g)

    print("Graph: 3x3 Grid (A-I)")
    print("Normal path A -> I:")
    path, cost = planner.find_route('A', 'I')
    print(f"Path: {path}, Cost: {cost}")

    print("\nPath A -> I avoiding 'E' (Center):")
    path, cost = planner.find_route('A', 'I', forbidden_nodes=['E'])
    print(f"Path: {path}, Cost: {cost}")

    print("\nPath A -> I visiting 'C' then 'G' (must_visit=['C', 'G']):")
    path, cost = planner.find_route('A', 'I', must_visit=['C', 'G'])
    print(f"Path: {path}, Cost: {cost}")

    print("\nPath A -> I visiting 'G' then 'C' (must_visit=['G', 'C']):")
    path, cost = planner.find_route('A', 'I', must_visit=['G', 'C'])
    print(f"Path: {path}, Cost: {cost}")

if __name__ == "__main__":
    main()
