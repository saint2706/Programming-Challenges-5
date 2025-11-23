package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
)

// Graph represents an undirected graph.
type Graph struct {
	Adj   map[int][]int
	Nodes int
}

// NewGraph creates a graph with n nodes (0 to n-1).
func NewGraph(n int) *Graph {
	return &Graph{
		Adj:   make(map[int][]int),
		Nodes: n,
	}
}

// AddEdge adds an undirected edge.
func (g *Graph) AddEdge(u, v int) {
	g.Adj[u] = append(g.Adj[u], v)
	g.Adj[v] = append(g.Adj[v], u)
}

// WeisfeilerLehmanHash computes a hash for the graph using the Weisfeiler-Lehman test.
// Iterations: typical heuristic value is related to diameter, but constant (e.g., 3-5) is often enough for simple cases.
func WeisfeilerLehmanHash(g *Graph, iterations int) string {
	// Initial labels: degree of each node
	labels := make([]string, g.Nodes)
	for i := 0; i < g.Nodes; i++ {
		labels[i] = fmt.Sprintf("%d", len(g.Adj[i]))
	}

	for iter := 0; iter < iterations; iter++ {
		newLabels := make([]string, g.Nodes)
		for i := 0; i < g.Nodes; i++ {
			// Collect neighbor labels
			neighborLabels := make([]string, 0, len(g.Adj[i]))
			for _, neighbor := range g.Adj[i] {
				neighborLabels = append(neighborLabels, labels[neighbor])
			}
			sort.Strings(neighborLabels)

			// Construct signature: current_label + neighbors
			signature := labels[i] + "(" + strings.Join(neighborLabels, ",") + ")"
			newLabels[i] = hash(signature)
		}

		// Compression mapping could be used here to keep labels short,
		// but hashing strings is easier to implement.
		labels = newLabels
	}

	// Final graph signature: sorted list of all node labels
	sort.Strings(labels)
	finalSig := strings.Join(labels, "|")
	return hash(finalSig)
}

func hash(s string) string {
	h := sha256.Sum256([]byte(s))
	return hex.EncodeToString(h[:])
}

// IsIsomorphic checks if two graphs are isomorphic using WL test.
// Returns heuristic result (false = definitely not, true = likely isomorphic).
func IsIsomorphic(g1, g2 *Graph) bool {
	if g1.Nodes != g2.Nodes {
		return false
	}
	// Heuristic iterations
	h1 := WeisfeilerLehmanHash(g1, 3)
	h2 := WeisfeilerLehmanHash(g2, 3)
	return h1 == h2
}
