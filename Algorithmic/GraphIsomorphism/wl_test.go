package main

import (
	"testing"
)

func TestGraphIsomorphism(t *testing.T) {
	// Graph 1: Triangle (0-1, 1-2, 2-0)
	g1 := NewGraph(3)
	g1.AddEdge(0, 1)
	g1.AddEdge(1, 2)
	g1.AddEdge(2, 0)

	// Graph 2: Triangle (0-2, 2-1, 1-0) - same structure, different edge order
	g2 := NewGraph(3)
	g2.AddEdge(0, 2)
	g2.AddEdge(2, 1)
	g2.AddEdge(1, 0)

	if !IsIsomorphic(g1, g2) {
		t.Error("Triangles should be isomorphic")
	}

	// Graph 3: Line (0-1, 1-2)
	g3 := NewGraph(3)
	g3.AddEdge(0, 1)
	g3.AddEdge(1, 2)

	if IsIsomorphic(g1, g3) {
		t.Error("Triangle and Line should not be isomorphic")
	}

	// Isomorphism check with relabeling
	// G4: Square (0-1, 1-2, 2-3, 3-0)
	g4 := NewGraph(4)
	g4.AddEdge(0, 1)
	g4.AddEdge(1, 2)
	g4.AddEdge(2, 3)
	g4.AddEdge(3, 0)

	// G5: Square with permuted labels
	// 0->2, 1->3, 2->0, 3->1
	// Edges: 2-3, 3-0, 0-1, 1-2
	g5 := NewGraph(4)
	g5.AddEdge(2, 3)
	g5.AddEdge(3, 0)
	g5.AddEdge(0, 1)
	g5.AddEdge(1, 2)

	if !IsIsomorphic(g4, g5) {
		t.Error("Squares should be isomorphic")
	}

	// Non-isomorphic same nodes/edges count
	// G6: Star (0 center, 1,2,3 leaves)
	g6 := NewGraph(4)
	g6.AddEdge(0, 1)
	g6.AddEdge(0, 2)
	g6.AddEdge(0, 3)

	if IsIsomorphic(g4, g6) {
		t.Error("Square and Star should not be isomorphic")
	}
}
