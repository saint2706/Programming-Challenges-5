# Dynamic Shortest Paths Service

A service for efficiently computing shortest paths in graphs where edge weights change over time, using incremental algorithms.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Dynamic shortest paths** maintains shortest path information as the graph changes, avoiding full recomputation.

### Algorithms
1. **D* Lite**: An incremental search algorithm that reuses previous search results
2. **LPA* (Lifelong Planning A*)**: Maintains shortest paths as costs change

### When to Use
- Navigation systems with traffic updates
- Network routing with link failures
- Game AI with changing terrain costs

### Key Insight
When an edge weight changes, only paths using that edge may need updates. By maintaining additional bookkeeping, we can update only affected paths.

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use dynamic_shortest_paths_service::{Graph, DynamicSP};

// Create graph
let mut graph = Graph::new(100);
graph.add_edge(0, 1, 5);
graph.add_edge(1, 2, 3);

// Initialize dynamic shortest paths
let mut dsp = DynamicSP::new(&graph, 0);  // source = 0

// Get initial path
let path = dsp.shortest_path(2);

// Update edge weight
graph.update_edge(1, 2, 10);
dsp.update_edge(1, 2, 10);

// Get updated path (incremental update)
let new_path = dsp.shortest_path(2);
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Initial computation** | $O(E \log V)$ |
| **Edge update** | $O(k \log V)$ |

Where:
- $V$ = number of vertices
- $E$ = number of edges
- $k$ = number of affected vertices (typically $k \ll V$)

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
