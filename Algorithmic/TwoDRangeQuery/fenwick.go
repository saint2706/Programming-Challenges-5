package main

import (
	"errors"
)

// FenwickTree2D implements a 2D Binary Indexed Tree (BIT).
type FenwickTree2D struct {
	tree [][]int
	rows int
	cols int
}

// NewFenwickTree2D creates a new 2D BIT with given dimensions.
func NewFenwickTree2D(rows, cols int) *FenwickTree2D {
	t := make([][]int, rows+1)
	for i := range t {
		t[i] = make([]int, cols+1)
	}
	return &FenwickTree2D{
		tree: t,
		rows: rows,
		cols: cols,
	}
}

// Update adds delta to the element at (r, c).
// 0-based indexing for input, handled internally as 1-based.
func (ft *FenwickTree2D) Update(r, c, delta int) error {
	if r < 0 || r >= ft.rows || c < 0 || c >= ft.cols {
		return errors.New("index out of bounds")
	}
	for i := r + 1; i <= ft.rows; i += i & -i {
		for j := c + 1; j <= ft.cols; j += j & -j {
			ft.tree[i][j] += delta
		}
	}
	return nil
}

// query returns the sum of the rectangle from (0, 0) to (r, c).
func (ft *FenwickTree2D) query(r, c int) int {
	sum := 0
	for i := r + 1; i > 0; i -= i & -i {
		for j := c + 1; j > 0; j -= j & -j {
			sum += ft.tree[i][j]
		}
	}
	return sum
}

// Query returns the sum of the rectangle defined by (r1, c1) top-left and (r2, c2) bottom-right.
func (ft *FenwickTree2D) Query(r1, c1, r2, c2 int) (int, error) {
	if r1 < 0 || c1 < 0 || r2 >= ft.rows || c2 >= ft.cols || r1 > r2 || c1 > c2 {
		return 0, errors.New("invalid query range")
	}
	return ft.query(r2, c2) - ft.query(r1-1, c2) - ft.query(r2, c1-1) + ft.query(r1-1, c1-1), nil
}
