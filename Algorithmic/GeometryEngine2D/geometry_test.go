package main

import (
	"reflect"
	"testing"
)

func TestConvexHull(t *testing.T) {
	points := []Point{
		{0, 0}, {1, 1}, {2, 2}, // Collinear
		{0, 2}, {2, 0}, // Corners
		{1, 0.5}, // Inside
	}

	// Hull should be (0,0), (2,0), (2,2), (0,2) in CCW order starting from bottom-left-most?
	// Monotone chain starts with min-x, min-y.
	// Expected: (0,0), (2,0), (2,2), (0,2).

	hull := ConvexHull(points)
	if len(hull) != 4 {
		t.Errorf("Expected 4 points, got %d: %v", len(hull), hull)
	}

	// Check content roughly (order matters)
	// Lower hull: (0,0) -> (2,0) -> (2,2)
	// Upper hull: (2,2) -> (0,2) -> (0,0)
	// Result: (0,0), (2,0), (2,2), (0,2).
	want := []Point{{0, 0}, {2, 0}, {2, 2}, {0, 2}}
	if !reflect.DeepEqual(hull, want) {
		t.Errorf("Got %v, want %v", hull, want)
	}
}

func TestPointInPolygon(t *testing.T) {
	poly := []Point{{0, 0}, {2, 0}, {2, 2}, {0, 2}}

	// Inside
	if !IsPointInPolygon(Point{1, 1}, poly) {
		t.Error("(1,1) should be inside")
	}

	// Outside
	if IsPointInPolygon(Point{3, 3}, poly) {
		t.Error("(3,3) should be outside")
	}

	// On edge (Ray casting logic varies, but typically inside or strict)
	// Standard ray casting with strictly > or < might be finicky on edges.
	// We won't strictly enforce edge behavior for this simple implementation.
}

func TestArea(t *testing.T) {
	poly := []Point{{0, 0}, {2, 0}, {2, 2}, {0, 2}}
	area := Area(poly)
	if area != 4.0 {
		t.Errorf("Area should be 4.0, got %f", area)
	}
}
