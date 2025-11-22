package binpacking

import (
	"errors"
	"sort"
)

// Bin represents a one-dimensional bin.
type Bin struct {
	Capacity  float64
	Remaining float64
	Items     []float64
}

// NewBin creates a bin with given capacity.
func NewBin(capacity float64) Bin {
	return Bin{Capacity: capacity, Remaining: capacity}
}

// Add attempts to place an item in the bin.
func (b *Bin) Add(item float64) bool {
	if item < 0 {
		return false
	}
	if b.Remaining+1e-9 < item { // allow small floating error buffer
		return false
	}
	b.Items = append(b.Items, item)
	b.Remaining -= item
	return true
}

// Bins is a slice helper for stats.
type Bins []Bin

// Utilization returns total usage fraction across bins.
func (bins Bins) Utilization() float64 {
	if len(bins) == 0 {
		return 0
	}
	used := 0.0
	capacity := 0.0
	for _, b := range bins {
		used += b.Capacity - b.Remaining
		capacity += b.Capacity
	}
	if capacity == 0 {
		return 0
	}
	return used / capacity
}

// FirstFit applies the classic first-fit heuristic.
func FirstFit(capacity float64, items []float64) (Bins, error) {
	if capacity <= 0 {
		return nil, errors.New("capacity must be positive")
	}
	var bins Bins
	for _, item := range items {
		if item < 0 || item > capacity+1e-9 {
			return nil, errors.New("item does not fit in bin or negative")
		}
		placed := false
		for i := range bins {
			if bins[i].Add(item) {
				placed = true
				break
			}
		}
		if !placed {
			bin := NewBin(capacity)
			bin.Add(item)
			bins = append(bins, bin)
		}
	}
	return bins, nil
}

// BestFit places each item into the bin with least remaining space where it fits.
func BestFit(capacity float64, items []float64) (Bins, error) {
	if capacity <= 0 {
		return nil, errors.New("capacity must be positive")
	}
	var bins Bins
	for _, item := range items {
		if item < 0 || item > capacity+1e-9 {
			return nil, errors.New("item does not fit in bin or negative")
		}
		bestIdx := -1
		bestRemaining := capacity + 1 // start larger than capacity
		for i := range bins {
			if bins[i].Remaining+1e-9 >= item {
				remaining := bins[i].Remaining - item
				if remaining < bestRemaining {
					bestRemaining = remaining
					bestIdx = i
				}
			}
		}
		if bestIdx == -1 {
			bin := NewBin(capacity)
			bin.Add(item)
			bins = append(bins, bin)
		} else {
			bins[bestIdx].Add(item)
		}
	}
	return bins, nil
}

// FirstFitDecreasing sorts items descending before applying FirstFit.
func FirstFitDecreasing(capacity float64, items []float64) (Bins, error) {
	sorted := append([]float64(nil), items...)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i] > sorted[j]
	})
	return FirstFit(capacity, sorted)
}

// BinAssignment returns a simple view of bin contents for reporting.
func BinAssignment(bins Bins) [][]float64 {
	assignment := make([][]float64, len(bins))
	for i, b := range bins {
		assignment[i] = append([]float64(nil), b.Items...)
	}
	return assignment
}
