"""Route planning with constraints using modified Dijkstra's algorithm.

This module provides route planning capabilities with support for:
- Required waypoints (must-visit nodes)
- Forbidden nodes and edges
- Shortest path computation via Dijkstra's algorithm
"""
import heapq
from typing import List, Dict, Set, Tuple, Optional, Any


class Graph:
    """Weighted graph representation using adjacency lists."""

    def __init__(self):
        # Adjacency list: node -> list of (neighbor, weight)
        self.adj: Dict[str, List[Tuple[str, float]]] = {}

    def add_edge(self, u: str, v: str, weight: float, directed: bool = False):
        """Add an edge to the graph.

        Args:
            u: Source node.
            v: Destination node.
            weight: Edge weight/cost.
            directed: If True, add only u->v; otherwise add both directions.
        """
        if u not in self.adj:
            self.adj[u] = []
        if v not in self.adj:
            self.adj[v] = []

        self.adj[u].append((v, weight))
        if not directed:
            self.adj[v].append((u, weight))


class RoutePlanner:
    """Route planner supporting constrained shortest path queries."""

    def __init__(self, graph: Graph):
        """Initialize with a graph.

        Args:
            graph: The graph to plan routes on.
        """
        self.graph = graph

    def dijkstra(self, start: str, end: Optional[str] = None, forbidden_nodes: Set[str] = None, forbidden_edges: Set[Tuple[str, str]] = None) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Run Dijkstra's algorithm with optional constraints.

        Args:
            start: Starting node.
            end: Optional target node (stops early if reached).
            forbidden_nodes: Nodes to exclude from paths.
            forbidden_edges: Edges to exclude from paths.

        Returns:
            Tuple of (distances dict, predecessors dict).
        """
        if forbidden_nodes is None:
            forbidden_nodes = set()
        if forbidden_edges is None:
            forbidden_edges = set()

        distances = {node: float('inf') for node in self.graph.adj}
        distances[start] = 0
        predecessors = {node: None for node in self.graph.adj}

        pq = [(0, start)]

        while pq:
            d, u = heapq.heappop(pq)

            if d > distances[u]:
                continue

            if u == end:
                break

            for v, weight in self.graph.adj.get(u, []):
                if v in forbidden_nodes:
                    continue
                if (u, v) in forbidden_edges or (v, u) in forbidden_edges:
                    continue

                new_dist = d + weight
                if new_dist < distances.get(v, float('inf')):
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(pq, (new_dist, v))

        return distances, predecessors

    def reconstruct_path(self, predecessors: Dict[str, str], start: str, end: str) -> List[str]:
        """Reconstruct the path from start to end using predecessors dict."""
        path = []
        curr = end
        while curr is not None:
            path.append(curr)
            if curr == start:
                break
            curr = predecessors.get(curr)

        if path[-1] != start:
            return [] # No path found
        return path[::-1]

    def find_route(self, start: str, end: str, must_visit: List[str] = None, forbidden_nodes: List[str] = None, forbidden_edges: List[Tuple[str, str]] = None) -> Tuple[List[str], float]:
        """
        Finds a route from start to end passing through all nodes in must_visit (in order)
        while avoiding forbidden nodes/edges.

        Args:
            start: Start node.
            end: End node.
            must_visit: List of nodes to visit in specific order.
            forbidden_nodes: List of nodes to avoid.
            forbidden_edges: List of edges (u, v) to avoid.

        Returns:
            (path, total_cost)
        """
        if must_visit is None: must_visit = []
        if forbidden_nodes is None: forbidden_nodes = []
        if forbidden_edges is None: forbidden_edges = []

        forbidden_nodes_set = set(forbidden_nodes)
        forbidden_edges_set = set(forbidden_edges)

        # Sequence of points to visit: Start -> M1 -> M2 ... -> Mn -> End
        waypoints = [start] + must_visit + [end]

        full_path = []
        total_cost = 0.0

        for i in range(len(waypoints) - 1):
            u = waypoints[i]
            v = waypoints[i+1]

            # Find shortest path from u to v
            dists, preds = self.dijkstra(u, v, forbidden_nodes_set, forbidden_edges_set)

            if dists.get(v) == float('inf'):
                return [], float('inf') # Path broken

            segment = self.reconstruct_path(preds, u, v)

            # Append segment to full_path
            # Note: segment includes u and v.
            # If we just append, we duplicate the join points (M1, M2...)
            if i == 0:
                full_path.extend(segment)
            else:
                full_path.extend(segment[1:]) # Skip the first element as it's the same as last of prev segment

            total_cost += dists[v]

        return full_path, total_cost
