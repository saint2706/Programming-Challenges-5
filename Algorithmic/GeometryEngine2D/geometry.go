package main

import (
	"math"
	"sort"
)

// Point represents a 2D point.
type Point struct {
	X, Y float64
}

// CrossProduct returns the cross product of vectors OA and OB.
// Positive if O->A->B is counter-clockwise.
// Negative if clockwise.
// Zero if collinear.
func CrossProduct(o, a, b Point) float64 {
	return (a.X-o.X)*(b.Y-o.Y) - (a.Y-o.Y)*(b.X-o.X)
}

// ConvexHull computes the convex hull of a set of points using Monotone Chain algorithm.
// Returns points in counter-clockwise order.
func ConvexHull(points []Point) []Point {
	n := len(points)
	if n <= 2 {
		return points
	}

	// Sort by X, then Y
	sort.Slice(points, func(i, j int) bool {
		if points[i].X == points[j].X {
			return points[i].Y < points[j].Y
		}
		return points[i].X < points[j].X
	})

	// Build lower hull
	lower := []Point{}
	for _, p := range points {
		for len(lower) >= 2 && CrossProduct(lower[len(lower)-2], lower[len(lower)-1], p) <= 0 {
			lower = lower[:len(lower)-1]
		}
		lower = append(lower, p)
	}

	// Build upper hull
	upper := []Point{}
	for i := n - 1; i >= 0; i-- {
		p := points[i]
		for len(upper) >= 2 && CrossProduct(upper[len(upper)-2], upper[len(upper)-1], p) <= 0 {
			upper = upper[:len(upper)-1]
		}
		upper = append(upper, p)
	}

	// Concatenate (remove duplicate start/end points)
	return append(lower[:len(lower)-1], upper[:len(upper)-1]...)
}

// IsPointInPolygon checks if point p is inside the polygon using Ray Casting algorithm.
// Polygon vertices should be ordered (CW or CCW).
func IsPointInPolygon(p Point, polygon []Point) bool {
	n := len(polygon)
	inside := false
	j := n - 1
	for i := 0; i < n; i++ {
		// Check if ray crosses edge (polygon[i], polygon[j])
		if ((polygon[i].Y > p.Y) != (polygon[j].Y > p.Y)) &&
			(p.X < (polygon[j].X-polygon[i].X)*(p.Y-polygon[i].Y)/(polygon[j].Y-polygon[i].Y)+polygon[i].X) {
			inside = !inside
		}
		j = i
	}
	return inside
}

// Area calculates the polygon area using the shoelace formula.
func Area(polygon []Point) float64 {
	area := 0.0
	n := len(polygon)
	j := n - 1
	for i := 0; i < n; i++ {
		area += (polygon[j].X + polygon[i].X) * (polygon[j].Y - polygon[i].Y)
		j = i
	}
	return math.Abs(area / 2.0)
}
