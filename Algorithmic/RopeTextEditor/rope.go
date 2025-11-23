package main

import (
	"fmt"
)

// RopeNode represents a node in the Rope tree.
type RopeNode struct {
	Left   *RopeNode
	Right  *RopeNode
	Weight int    // Weight of the left subtree (length of string in left child)
	Value  string // Only used if leaf
	IsLeaf bool
}

// Rope represents the text editor core structure.
type Rope struct {
	Root *RopeNode
}

// NewRope creates a rope from a string.
func NewRope(s string) *Rope {
	// For simplicity, create a single leaf. Real usage might chunk it.
	return &Rope{
		Root: &RopeNode{
			Value:  s,
			Weight: len(s),
			IsLeaf: true,
		},
	}
}

// Length returns the total length of the rope.
func (r *Rope) Length() int {
	return lengthRecursive(r.Root)
}

func lengthRecursive(n *RopeNode) int {
	if n == nil {
		return 0
	}
	if n.IsLeaf {
		return len(n.Value)
	}
	return n.Weight + lengthRecursive(n.Right)
}

// String converts the rope back to a string.
func (r *Rope) String() string {
	return stringRecursive(r.Root)
}

func stringRecursive(n *RopeNode) string {
	if n == nil {
		return ""
	}
	if n.IsLeaf {
		return n.Value
	}
	return stringRecursive(n.Left) + stringRecursive(n.Right)
}

// Index returns the character at index i.
func (r *Rope) Index(i int) (byte, error) {
	if i < 0 || i >= r.Length() {
		return 0, fmt.Errorf("index out of bounds")
	}
	return indexRecursive(r.Root, i), nil
}

func indexRecursive(n *RopeNode, i int) byte {
	if n.IsLeaf {
		return n.Value[i]
	}
	if i < n.Weight {
		return indexRecursive(n.Left, i)
	}
	return indexRecursive(n.Right, i-n.Weight)
}

// Concat concatenates two ropes.
func Concat(r1, r2 *Rope) *Rope {
	// Simplification: just create a new root.
	// Ideally we balance.
	newRoot := &RopeNode{
		Left:   r1.Root,
		Right:  r2.Root,
		Weight: r1.Length(),
		IsLeaf: false,
	}
	return &Rope{Root: newRoot}
}

// Split splits the rope at index i into two ropes.
func (r *Rope) Split(i int) (*Rope, *Rope) {
	if i == 0 {
		return NewRope(""), r
	}
	if i == r.Length() {
		return r, NewRope("")
	}

	leftRoot, rightRoot := splitRecursive(r.Root, i)
	return &Rope{Root: leftRoot}, &Rope{Root: rightRoot}
}

func splitRecursive(n *RopeNode, i int) (*RopeNode, *RopeNode) {
	if n.IsLeaf {
		return &RopeNode{Value: n.Value[:i], Weight: i, IsLeaf: true},
		       &RopeNode{Value: n.Value[i:], Weight: len(n.Value) - i, IsLeaf: true}
	}

	if i < n.Weight {
		// Split happens in the left child
		ll, lr := splitRecursive(n.Left, i)
		// New Left Node uses just the left part of the split
		newLeft := ll
		// New Right Node combines the right part of the split with the original right child
		newRight := &RopeNode{
			Left:   lr,
			Right:  n.Right,
			Weight: lengthRecursive(lr), // Recompute weight
			IsLeaf: false,
		}
		return newLeft, newRight
	} else {
		// Split happens in the right child
		rl, rr := splitRecursive(n.Right, i-n.Weight)
		// New Left Node combines original left with left part of split
		newLeft := &RopeNode{
			Left:   n.Left,
			Right:  rl,
			Weight: n.Weight,
			IsLeaf: false,
		}
		// New Right Node uses just the right part of split
		newRight := rr
		return newLeft, newRight
	}
}

// Insert inserts string s at index i.
func (r *Rope) Insert(i int, s string) *Rope {
	left, right := r.Split(i)
	middle := NewRope(s)
	return Concat(Concat(left, middle), right)
}

// Delete deletes characters from start to end.
func (r *Rope) Delete(start, end int) *Rope {
	left, temp := r.Split(start)
	_, right := temp.Split(end - start)
	return Concat(left, right)
}
