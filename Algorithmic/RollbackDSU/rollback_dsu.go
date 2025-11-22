package rollbackdsu

import "fmt"

// RollbackDSU implements a disjoint set union data structure that supports
// rollback to any recorded snapshot. Path compression is intentionally omitted
// so that previous states can be restored accurately.
type RollbackDSU struct {
	parent  []int
	size    []int
	history []change
}

type change struct {
	child      int
	parentRoot int
	oldParent  int
	oldSize    int
}

// NewRollbackDSU initializes a rollback-capable DSU with n elements numbered
// from 0 to n-1. Each element starts in its own component.
func NewRollbackDSU(n int) *RollbackDSU {
	if n <= 0 {
		panic("number of elements must be positive")
	}

	parent := make([]int, n)
	size := make([]int, n)
	for i := 0; i < n; i++ {
		parent[i] = i
		size[i] = 1
	}

	return &RollbackDSU{parent: parent, size: size}
}

// Find returns the representative of the set containing x. Path compression is
// intentionally not used so that the structure can be rolled back precisely.
func (d *RollbackDSU) Find(x int) int {
	for x != d.parent[x] {
		x = d.parent[x]
	}
	return x
}

// Union merges the sets containing a and b using union by size. If the sets
// are already connected, Union returns false and does nothing. Otherwise it
// returns true.
func (d *RollbackDSU) Union(a, b int) bool {
	rootA := d.Find(a)
	rootB := d.Find(b)
	if rootA == rootB {
		return false
	}

	// Union by size keeps the tree shallow without path compression.
	if d.size[rootA] < d.size[rootB] {
		rootA, rootB = rootB, rootA
	}

	d.recordChange(rootA, rootB)
	d.parent[rootB] = rootA
	d.size[rootA] += d.size[rootB]
	return true
}

func (d *RollbackDSU) recordChange(parentRoot, child int) {
	d.history = append(d.history, change{
		child:      child,
		parentRoot: parentRoot,
		oldParent:  d.parent[child],
		oldSize:    d.size[parentRoot],
	})
}

// Snapshot records the current point in time and returns a handle that can be
// used to rollback to this state later.
func (d *RollbackDSU) Snapshot() int {
	return len(d.history)
}

// Rollback restores the DSU to the provided snapshot. It returns an error if
// the snapshot is invalid.
func (d *RollbackDSU) Rollback(snapshot int) error {
	if snapshot < 0 || snapshot > len(d.history) {
		return fmt.Errorf("invalid snapshot %d", snapshot)
	}

	for len(d.history) > snapshot {
		lastIndex := len(d.history) - 1
		ch := d.history[lastIndex]
		d.parent[ch.child] = ch.oldParent
		d.size[ch.parentRoot] = ch.oldSize
		d.history = d.history[:lastIndex]
	}
	return nil
}

// Size returns the size of the component containing x.
func (d *RollbackDSU) Size(x int) int {
	return d.size[d.Find(x)]
}

// Connected reports whether a and b belong to the same component.
func (d *RollbackDSU) Connected(a, b int) bool {
	return d.Find(a) == d.Find(b)
}
