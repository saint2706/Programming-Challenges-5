"""
Dimensionality-agnostic k-d tree implementation with median splitting and
priority-queue backtracking search.
"""
from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

Point = Sequence[float]
DistanceFn = Callable[[Point, Point], float]


def euclidean_distance(a: Point, b: Point) -> float:
    return hypot(*[x - y for x, y in zip(a, b)])


@dataclass
class KDNode:
    point: Point
    axis: int
    left: Optional["KDNode"]
    right: Optional["KDNode"]
    bounds_min: Point
    bounds_max: Point

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def _compute_bounds(points: List[Point]) -> Tuple[List[float], List[float]]:
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
    points_list = list(points)
    if not points_list:
        return None

    axis = depth % len(points_list[0])
    points_list.sort(key=lambda p: p[axis])
    median_index = len(points_list) // 2
    median_point = points_list[median_index]

    left_points = points_list[:median_index]
    right_points = points_list[median_index + 1 :]

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
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _bounds_distance(point: Point, bounds_min: Point, bounds_max: Point) -> float:
    """Squared distance from point to bounding box (0 if inside box)."""
    dist = 0.0
    for coord, min_val, max_val in zip(point, bounds_min, bounds_max):
        if coord < min_val:
            dist += (min_val - coord) ** 2
        elif coord > max_val:
            dist += (coord - max_val) ** 2
    return dist


def nearest_neighbor(
    root: Optional[KDNode], query: Point, distance_fn: DistanceFn = euclidean_distance
) -> Optional[Tuple[Point, float]]:
    """Find the single nearest neighbor using branch-and-bound search."""
    if root is None:
        return None

    best: Tuple[float, Point] = (float("inf"), root.point)
    heap: List[Tuple[float, KDNode]] = []

    def visit(node: KDNode):
        nonlocal best
        dist_sq = _squared_distance(query, node.point)
        if dist_sq < best[0]:
            best = (dist_sq, node.point)

        left = node.left
        right = node.right
        if left is not None:
            heappush(heap, (_bounds_distance(query, left.bounds_min, left.bounds_max), left))
        if right is not None:
            heappush(heap, (_bounds_distance(query, right.bounds_min, right.bounds_max), right))

    visit(root)

    while heap:
        bound, node = heappop(heap)
        if bound > best[0]:
            continue
        visit(node)

    return best[1], distance_fn(query, best[1])


def k_nearest_neighbors(
    root: Optional[KDNode], query: Point, k: int, distance_fn: DistanceFn = euclidean_distance
) -> List[Tuple[Point, float]]:
    """Return the k nearest neighbors ordered by distance."""
    if root is None or k <= 0:
        return []

    best_heap: List[Tuple[float, Point]] = []  # max-heap using negative distance
    node_queue: List[Tuple[float, KDNode]] = []  # min-heap ordered by bound distance

    def consider_point(point: Point):
        dist_sq = _squared_distance(query, point)
        if len(best_heap) < k:
            heappush(best_heap, (-dist_sq, point))
        elif dist_sq < -best_heap[0][0]:
            heappop(best_heap)
            heappush(best_heap, (-dist_sq, point))

    def push_child(node: Optional[KDNode]):
        if node is None:
            return
        bound = _bounds_distance(query, node.bounds_min, node.bounds_max)
        heappush(node_queue, (bound, node))

    push_child(root)

    while node_queue:
        bound, node = heappop(node_queue)
        if len(best_heap) == k and bound > -best_heap[0][0]:
            continue

        consider_point(node.point)
        push_child(node.left)
        push_child(node.right)

    results = [(-d, p) for d, p in best_heap]
    results.sort(key=lambda item: item[0])
    return [(point, distance_fn(query, point)) for _, point in results]


def brute_force_nearest(
    points: Iterable[Point], query: Point, distance_fn: DistanceFn = euclidean_distance
) -> Tuple[Point, float]:
    best_point = None
    best_dist_sq = float("inf")
    for p in points:
        dist_sq = _squared_distance(query, p)
        if dist_sq < best_dist_sq:
            best_point = p
            best_dist_sq = dist_sq
    return best_point, distance_fn(query, best_point)


def brute_force_k_nearest(
    points: Iterable[Point], query: Point, k: int, distance_fn: DistanceFn = euclidean_distance
) -> List[Tuple[Point, float]]:
    distances = [(_squared_distance(query, p), p) for p in points]
    distances.sort(key=lambda x: x[0])
    top = distances[:k]
    return [(p, distance_fn(query, p)) for _, p in top]


def tree_height(node: Optional[KDNode]) -> int:
    if node is None:
        return 0
    return 1 + max(tree_height(node.left), tree_height(node.right))


def count_nodes(node: Optional[KDNode]) -> int:
    if node is None:
        return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)
