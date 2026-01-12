package main

import (
	"fmt"
)

// PersistentVector implements a persistent array using a tree structure with path copying.
// We use a simple Binary Tree logic here.

// Node represents a node in the persistent tree.
type Node struct {
	Value  int // Only used if IsLeaf is true
	Left   *Node
	Right  *Node
	Size   int // Number of elements in the subtree
	IsLeaf bool
}

// PersistentArray represents the handle to a specific version of the array.
type PersistentArray struct {
	Root *Node
	Size int
}

// NewPersistentArray creates an empty array.
func NewPersistentArray() *PersistentArray {
	return &PersistentArray{
		Root: nil,
		Size: 0,
	}
}

// buildTree constructs a balanced tree from a slice.
func buildTree(data []int) *Node {
	if len(data) == 0 {
		return nil
	}
	if len(data) == 1 {
		return &Node{Value: data[0], IsLeaf: true, Size: 1}
	}
	mid := len(data) / 2
	left := buildTree(data[:mid])
	right := buildTree(data[mid:])
	return &Node{
		Left:   left,
		Right:  right,
		Size:   left.Size + right.Size,
		IsLeaf: false,
	}
}

// NewFromArray creates a PersistentArray from a go slice.
func NewFromArray(data []int) *PersistentArray {
	return &PersistentArray{
		Root: buildTree(data),
		Size: len(data),
	}
}

// Get retrieves the value at index i.
func (pa *PersistentArray) Get(i int) (int, error) {
	if i < 0 || i >= pa.Size {
		return 0, fmt.Errorf("index out of bounds: %d (size %d)", i, pa.Size)
	}
	return getRecursive(pa.Root, i), nil
}

func getRecursive(node *Node, i int) int {
	if node.IsLeaf {
		return node.Value
	}
	leftSize := 0
	if node.Left != nil {
		leftSize = node.Left.Size
	}

	if i < leftSize {
		return getRecursive(node.Left, i)
	}
	return getRecursive(node.Right, i-leftSize)
}

// Set updates the value at index i and returns a NEW PersistentArray.
func (pa *PersistentArray) Set(i int, val int) (*PersistentArray, error) {
	if i < 0 || i >= pa.Size {
		return nil, fmt.Errorf("index out of bounds: %d (size %d)", i, pa.Size)
	}
	newRoot := setRecursive(pa.Root, i, val)
	return &PersistentArray{
		Root: newRoot,
		Size: pa.Size,
	}, nil
}

func setRecursive(node *Node, i int, val int) *Node {
	// Path copying: create a new node
	newNode := &Node{
		Value:  node.Value,
		Left:   node.Left,
		Right:  node.Right,
		Size:   node.Size,
		IsLeaf: node.IsLeaf,
	}

	if node.IsLeaf {
		newNode.Value = val
		return newNode
	}

	leftSize := 0
	if node.Left != nil {
		leftSize = node.Left.Size
	}

	if i < leftSize {
		newNode.Left = setRecursive(node.Left, i, val)
	} else {
		newNode.Right = setRecursive(node.Right, i-leftSize, val)
	}
	return newNode
}

// Push adds an element to the end and returns a new PersistentArray.
func (pa *PersistentArray) Push(val int) *PersistentArray {
	return pa.pushBinaryTrie(val)
}

func (pa *PersistentArray) pushBinaryTrie(val int) *PersistentArray {
	// Determine required depth
	idx := pa.Size

	// If root is nil
	if pa.Root == nil {
		return &PersistentArray{Root: &Node{Value: val, IsLeaf: true, Size: 1}, Size: 1}
	}

	root := pa.Root
	height := 0
	curr := root
	for !curr.IsLeaf {
		height++
		curr = curr.Left
	}
	capacity := 1 << height

	var newRoot *Node

	if idx < capacity {
		// Fits in current tree structure
		newRoot = insertIntoTrie(root, height, idx, val)
	} else {
		// Need to grow. Old root becomes left child of new root.
		// New root height = height + 1
		newRoot = &Node{
			Left:   root,
			Right:  createPath(height, val), // Create a tree of height `height` with item at index 0 (relative)
			Size:   root.Size + 1,
			IsLeaf: false,
		}
	}

	return &PersistentArray{
		Root: newRoot,
		Size: pa.Size + 1,
	}
}

func createPath(height int, val int) *Node {
	if height == 0 {
		return &Node{Value: val, IsLeaf: true, Size: 1}
	}
	return &Node{
		Left:   createPath(height-1, val),
		Right:  nil, // Empty
		Size:   1,
		IsLeaf: false,
	}
}

func insertIntoTrie(node *Node, height int, idx int, val int) *Node {
	// Copy node
	newNode := &Node{
		Value:  node.Value,
		Left:   node.Left,
		Right:  node.Right,
		Size:   node.Size + 1, // We are adding one element
		IsLeaf: node.IsLeaf,
	}

	if height == 0 {
		newNode.Value = val
		newNode.IsLeaf = true
		newNode.Size = 1
		return newNode
	}

	// Determine direction based on index and height
	// The capacity of the left subtree is 2^(height-1)
	halfCap := 1 << (height - 1)

	if idx < halfCap {
		// Go Left
		if node.Left == nil {
			newNode.Left = createPath(height-1, val)
		} else {
			newNode.Left = insertIntoTrie(node.Left, height-1, idx, val)
		}
	} else {
		// Go Right
		if node.Right == nil {
			newNode.Right = createPath(height-1, val) // FIX: Pass val directly, do not subtract
		} else {
			newNode.Right = insertIntoTrie(node.Right, height-1, idx-halfCap, val)
		}
	}
	return newNode
}
