"""Polygon triangulation using the Ear Clipping algorithm.

This module provides functions to triangulate simple polygons by iteratively
finding and removing "ear" vertices. The algorithm runs in O(n^2) time.
"""

from typing import List, Tuple


class Point:
    """2D point representation."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


def is_convex(p: Point, prev_p: Point, next_p: Point) -> bool:
    """
    Check if the vertex p is convex (interior angle < 180).
    Using cross product of (p - prev_p) and (next_p - p).
    """
    # Vector prev -> p
    v1_x, v1_y = p.x - prev_p.x, p.y - prev_p.y
    # Vector p -> next
    v2_x, v2_y = next_p.x - p.x, next_p.y - p.y

    # Cross product
    cross = v1_x * v2_y - v1_y * v2_x

    # Assuming counter-clockwise winding
    return cross > 0


def is_point_inside_triangle(pt: Point, v1: Point, v2: Point, v3: Point) -> bool:
    """Checks if point pt is inside the triangle v1-v2-v3."""

    def sign(p1, p2, p3):
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

    d1 = sign(pt, v1, v2)
    d2 = sign(pt, v2, v3)
    d3 = sign(pt, v3, v1)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)


def triangulate_polygon(
    coords: List[Tuple[float, float]],
) -> List[Tuple[int, int, int]]:
    """
    Triangulates a simple polygon using the Ear Clipping algorithm.

    Args:
        coords: List of (x, y) tuples representing vertices in CCW order.

    Returns:
        List of triangles, where each triangle is a tuple of 3 indices into `coords`.
    """
    n = len(coords)
    if n < 3:
        return []

    # Store vertices as objects for easier manipulation, but keep original indices
    vertices = [(Point(x, y), i) for i, (x, y) in enumerate(coords)]

    triangles = []

    # Main loop: remove ears until we have a triangle left
    while len(vertices) > 3:
        ear_found = False
        n_curr = len(vertices)

        for i in range(n_curr):
            prev_v, prev_idx = vertices[(i - 1) % n_curr]
            curr_v, curr_idx = vertices[i]
            next_v, next_idx = vertices[(i + 1) % n_curr]

            # Check convexity
            if is_convex(curr_v, prev_v, next_v):
                # Check if any other vertex is inside this potential ear
                is_ear = True
                for j in range(n_curr):
                    if j == (i - 1) % n_curr or j == i or j == (i + 1) % n_curr:
                        continue

                    other_v, _ = vertices[j]
                    if is_point_inside_triangle(other_v, prev_v, curr_v, next_v):
                        is_ear = False
                        break

                if is_ear:
                    # Clip the ear
                    triangles.append((prev_idx, curr_idx, next_idx))
                    vertices.pop(i)
                    ear_found = True
                    break

        if not ear_found:
            raise ValueError(
                "Polygon is likely not simple or not CCW, or numerical issue."
            )

    # Add the final triangle
    triangles.append((vertices[0][1], vertices[1][1], vertices[2][1]))

    return triangles
