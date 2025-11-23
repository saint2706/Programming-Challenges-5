package main

import (
	"testing"
)

func TestFenwickTree2D(t *testing.T) {
	rows, cols := 4, 4
	ft := NewFenwickTree2D(rows, cols)

	// 1. Update (1, 1) with 5
	if err := ft.Update(1, 1, 5); err != nil {
		t.Errorf("Update failed: %v", err)
	}

	// 2. Query (1, 1) to (1, 1) should be 5
	val, err := ft.Query(1, 1, 1, 1)
	if err != nil {
		t.Errorf("Query failed: %v", err)
	}
	if val != 5 {
		t.Errorf("Expected 5, got %d", val)
	}

	// 3. Update (2, 2) with 10
	ft.Update(2, 2, 10)

	// 4. Query full range (0,0) to (3,3)
	// Should be 5 + 10 = 15
	val, _ = ft.Query(0, 0, 3, 3)
	if val != 15 {
		t.Errorf("Expected 15, got %d", val)
	}

	// 5. Query partial range (0,0) to (1,2)
	// Includes (1,1) but not (2,2). Should be 5.
	val, _ = ft.Query(0, 0, 1, 2)
	if val != 5 {
		t.Errorf("Expected 5, got %d", val)
	}

	// 6. Update (1, 2) with 3.
	// Grid:
	// . . . .
	// . 5 3 .
	// . . 10 .
	// . . . .
	ft.Update(1, 2, 3)

	// Query (1,1) to (2,2). Sum = 5 + 3 + 10 = 18
	val, _ = ft.Query(1, 1, 2, 2)
	if val != 18 {
		t.Errorf("Expected 18, got %d", val)
	}

	// Test invalid queries
	_, err = ft.Query(2, 2, 1, 1) // r1 > r2
	if err == nil {
		t.Error("Expected error for invalid range")
	}
}
