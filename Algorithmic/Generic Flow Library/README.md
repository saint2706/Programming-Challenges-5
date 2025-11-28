# Generic Flow Library

A library for solving maximum flow and minimum cut problems on flow networks using the Edmonds-Karp algorithm.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Maximum flow** finds the maximum amount of "flow" that can be sent from a source to a sink in a flow network.

### Key Concepts
- **Flow network**: Directed graph where each edge has a capacity
- **Flow**: Assignment of values to edges respecting capacities
- **Residual graph**: Shows remaining capacity and allows flow reversal

### Edmonds-Karp Algorithm
A specific implementation of Ford-Fulkerson using BFS:
1. Find augmenting path using BFS (shortest path in residual graph)
2. Send maximum possible flow along the path
3. Update residual capacities
4. Repeat until no augmenting path exists

### Min-Cut Max-Flow Theorem
The maximum flow equals the minimum cut capacity.

**Min-cut**: Partition vertices into two sets (S, T) where source ∈ S, sink ∈ T, minimizing total capacity of edges from S to T.

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use generic_flow_library::{FlowNetwork, max_flow};

// Create network with 6 vertices
let mut network = FlowNetwork::new(6);

// Add edges with capacities
network.add_edge(0, 1, 16);
network.add_edge(0, 2, 13);
network.add_edge(1, 3, 12);
network.add_edge(2, 1, 4);
network.add_edge(2, 4, 14);
network.add_edge(3, 2, 9);
network.add_edge(3, 5, 20);
network.add_edge(4, 3, 7);
network.add_edge(4, 5, 4);

// Find max flow from source 0 to sink 5
let max = max_flow(&mut network, 0, 5);
println!("Maximum flow: {}", max);  // Output: 23

// Get min-cut
let cut = network.min_cut(0);
println!("Min-cut vertices: {:?}", cut);
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Edmonds-Karp** | $O(VE^2)$ |
| **Finding min-cut** | $O(V + E)$ |

Where:
- $V$ = number of vertices
- $E$ = number of edges

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
