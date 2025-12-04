"""Geometry Engine 2D.

Convex Hull (Monotone Chain), Point in Polygon (Ray Casting).
"""

from typing import List, Tuple

Point = Tuple[float, float]

def cross_product(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def convex_hull(points: List[Point]) -> List[Point]:
    """Compute Convex Hull using Monotone Chain algorithm. O(N log N)."""
    n = len(points)
    if n <= 2:
        return points

    points = sorted(points)

    upper = []
    for p in points:
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    lower = []
    for p in reversed(points):
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    return upper[:-1] + lower[:-1]

def point_in_polygon(poly: List[Point], p: Point) -> bool:
    """Check if point p is inside polygon poly (Ray Casting)."""
    x, y = p
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside
