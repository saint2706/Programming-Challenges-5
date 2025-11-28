"""Dimensionality-agnostic k-d tree implementation.

This module provides a K-Dimensional Tree (k-d tree) for organizing points in a
k-dimensional space. It supports efficient Nearest Neighbor and k-Nearest Neighbor
searches using median splitting and priority-queue backtracking.
"""
from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Union

# Type aliases
Point = Sequence[float]
DistanceFn = Callable[[Point, Point], float]


def euclidean_distance(a: Point, b: Point) -> float:
    """Calculate Euclidean distance between two points.

    Args:
        a: First point (sequence of coordinates).
        b: Second point (sequence of coordinates).

    Returns:
        float: The Euclidean distance.
    """
    return hypot(*[x - y for x, y in zip(a, b)])


@dataclass
class KDNode:
    """Node in the k-d tree.

    Attributes:
        point: The point stored at this node.
        axis: The axis (dimension) used to split at this node.
        left: Left child node (points < split value).
        right: Right child node (points >= split value).
        bounds_min: Minimum bounding box coordinates for the subtree.
        bounds_max: Maximum bounding box coordinates for the subtree.
    """

    point: Point
    axis: int
    left: Optional["KDNode"]
    right: Optional["KDNode"]
    bounds_min: Point
    bounds_max: Point

    def is_leaf(self) -> bool:
        """Check if the node is a leaf (no children).

        Returns:
            bool: True if leaf, False otherwise.
        """
        return self.left is None and self.right is None


def _compute_bounds(points: List[Point]) -> Tuple[List[float], List[float]]:
    """Compute the minimum and maximum bounds for a set of points.

    Args:
        points: List of points.

    Returns:
        Tuple[List[float], List[float]]: (min_coords, max_coords)
    """
    if not points:
        return [], []
    dims = len(points[0])
    mins = [float("inf")] * dims
    maxs = [float("-inf")] * dims
    for p in points:
        for i, val in enumerate(p):
            if val < mins[i]:
                mins[i] = val
            if val > maxs[i]:
                maxs[i] = val
    return mins, maxs


def build_kd_tree(points: Iterable[Point], depth: int = 0) -> Optional[KDNode]:
    """Build a k-d tree from a collection of points.

    Uses median splitting to ensure a balanced tree.

    Args:
        points: Iterable of points (sequences of floats).
        depth: Current depth in the tree (used to determine split axis).

    Returns:
        Optional[KDNode]: The root of the constructed tree.
    """
    points_list = list(points)
    if not points_list:
        return None

    # Determine splitting axis based on depth
    axis = depth % len(points_list[0])

    # Sort points by current axis to find median
    points_list.sort(key=lambda p: p[axis])
    median_index = len(points_list) // 2
    median_point = points_list[median_index]

    left_points = points_list[:median_index]
    right_points = points_list[median_index + 1 :]

    # Pre-compute bounds for pruning during search
    bounds_min, bounds_max = _compute_bounds(points_list)

    return KDNode(
        point=median_point,
        axis=axis,
        left=build_kd_tree(left_points, depth + 1) if left_points else None,
        right=build_kd_tree(right_points, depth + 1) if right_points else None,
        bounds_min=bounds_min,
        bounds_max=bounds_max,
    )


def _squared_distance(a: Point, b: Point) -> float:
    """Calculate squared Euclidean distance (faster for comparisons)."""
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _bounds_distance(
    point: Point, bounds_min: Point, bounds_max: Point
) -> float:
    """Calculate minimum squared distance from a point to a hyper-rectangle.

    Returns 0 if the point is inside the bounding box.
    """
    dist = 0.0
    for coord, min_val, max_val in zip(point, bounds_min, bounds_max):
        if coord < min_val:
            dist += (min_val - coord) ** 2
        elif coord > max_val:
            dist += (coord - max_val) ** 2
    return dist


def nearest_neighbor(
    root: Optional[KDNode],
    query: Point,
    distance_fn: DistanceFn = euclidean_distance,
) -> Optional[Tuple[Point, float]]:
    """Find the single nearest neighbor to a query point.

    Uses a branch-and-bound approach with a priority queue to prune search space.

    Args:
        root: The root of the k-d tree.
        query: The query point.
        distance_fn: Function to calculate actual distance for return value.

    Returns:
        Optional[Tuple[Point, float]]: (nearest_point, distance), or None if tree is empty.
    """
    if root is None:
        return None

    # (squared_distance, point)
    best: Tuple[float, Point] = (float("inf"), root.point)

    # Priority queue: (min_bound_dist_sq, node)
    heap: List[Tuple[float, KDNode]] = []

    def visit(node: KDNode) -> None:
        """
        Docstring for visit.
        """
        nonlocal best
        dist_sq = _squared_distance(query, node.point)
        if dist_sq < best[0]:
            best = (dist_sq, node.point)

        left = node.left
        right = node.right

        # Push children to heap with their lower bound distance
        if left is not None:
            bound_dist = _bounds_distance(
                query, left.bounds_min, left.bounds_max
            )
            heappush(heap, (bound_dist, left))
        if right is not None:
            bound_dist = _bounds_distance(
                query, right.bounds_min, right.bounds_max
            )
            heappush(heap, (bound_dist, right))

    visit(root)

    while heap:
        bound, node = heappop(heap)
        # If lower bound of subtree is further than current best, we can prune it
        if bound >= best[0]:
            continue
        visit(node)

    return best[1], distance_fn(query, best[1])


def k_nearest_neighbors(
    root: Optional[KDNode],
    query: Point,
    k: int,
    distance_fn: DistanceFn = euclidean_distance,
) -> List[Tuple[Point, float]]:
    """Find the k nearest neighbors to a query point.

    Args:
        root: The root of the k-d tree.
        query: The query point.
        k: The number of neighbors to find.
        distance_fn: Function to calculate actual distance for return values.

    Returns:
        List[Tuple[Point, float]]: List of (point, distance) sorted by distance.
    """
    if root is None or k <= 0:
        return []

    # Max-heap of k closest points found so far: (-dist_sq, point)
    # We use negative distance because Python's heapq is a min-heap
    best_heap: List[Tuple[float, Point]] = []

    # Min-heap for traversing nodes: (bound_dist_sq, node)
    node_queue: List[Tuple[float, KDNode]] = []

    def consider_point(point: Point) -> None:
        """
        Docstring for consider_point.
        """
        dist_sq = _squared_distance(query, point)
        if len(best_heap) < k:
            heappush(best_heap, (-dist_sq, point))
        elif dist_sq < -best_heap[0][0]:
            heappop(best_heap)
            heappush(best_heap, (-dist_sq, point))

    def push_child(node: Optional[KDNode]) -> None:
        """
        Docstring for push_child.
        """
        if node is None:
            return
        bound = _bounds_distance(query, node.bounds_min, node.bounds_max)
        heappush(node_queue, (bound, node))

    push_child(root)

    while node_queue:
        bound, node = heappop(node_queue)

        # If we have k points and this subtree is further than the k-th best, prune
        if len(best_heap) == k and bound >= -best_heap[0][0]:
            continue

        consider_point(node.point)
        push_child(node.left)
        push_child(node.right)

    # Convert back to positive distances and sort
    results = [(-d, p) for d, p in best_heap]
    results.sort(key=lambda item: item[0])

    return [(point, distance_fn(query, point)) for _, point in results]


def brute_force_nearest(
    points: Iterable[Point],
    query: Point,
    distance_fn: DistanceFn = euclidean_distance,
) -> Optional[Tuple[Point, float]]:
    """Find nearest neighbor using brute force search (for verification).

    Args:
        points: Iterable of points.
        query: The query point.
        distance_fn: Distance function.

    Returns:
        Optional[Tuple[Point, float]]: (nearest_point, distance).
    """
    points_list = list(points)
    if not points_list:
        return None

    best_point = points_list[0] # Default
    best_dist_sq = float("inf")

    # Iterate all to find min
    for p in points_list:
        dist_sq = _squared_distance(query, p)
        if dist_sq < best_dist_sq:
            best_point = p
            best_dist_sq = dist_sq

    return best_point, distance_fn(query, best_point)


def brute_force_k_nearest(
    points: Iterable[Point],
    query: Point,
    k: int,
    distance_fn: DistanceFn = euclidean_distance,
) -> List[Tuple[Point, float]]:
    """Find k nearest neighbors using brute force search.

    Args:
        points: Iterable of points.
        query: The query point.
        k: Number of neighbors.
        distance_fn: Distance function.

    Returns:
        List[Tuple[Point, float]]: List of (point, distance).
    """
    distances = [(_squared_distance(query, p), p) for p in points]
    distances.sort(key=lambda x: x[0])
    top = distances[:k]
    return [(p, distance_fn(query, p)) for _, p in top]


def tree_height(node: Optional[KDNode]) -> int:
    """Calculate the height of the tree.

    Args:
        node: Root node.

    Returns:
        int: Height of the tree (0 for empty).
    """
    if node is None:
        return 0
    return 1 + max(tree_height(node.left), tree_height(node.right))


def count_nodes(node: Optional[KDNode]) -> int:
    """Count total nodes in the tree.

    Args:
        node: Root node.

    Returns:
        int: Number of nodes.
    """
    if node is None:
        return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)
