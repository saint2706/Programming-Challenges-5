# Routing with Turn Penalties

Graph routing algorithm that considers turn costs in addition to edge weights, useful for vehicle routing and network optimization.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Turn penalty routing** extends shortest path algorithms to account for the cost of changing direction at nodes.

### Problem

In standard shortest path, only edge weights matter. But in reality:

- Vehicles lose time making turns
- Left turns are more costly than right turns
- U-turns may be prohibited

### Graph Transformation

Transform the graph so turns are represented:

**Method 1**: Edge-based graph

- Create a node for each edge in original graph
- Connect nodes if their edges share a vertex
- Edge weight = turn cost + destination edge weight

**Method 2**: Expanded state space

- State = (node, incoming_direction)
- Transitions include turn cost

### Algorithm

Run Dijkstra on the transformed graph.

## 💻 Installation

```bash
go build ./cmd/turnpenaltyrouting
go test
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "turnpenaltyrouting"
)

func main() {
    graph := NewGraph(5)

    // Add edges
    graph.AddEdge(0, 1, 10)
    graph.AddEdge(1, 2, 5)
    graph.AddEdge(0, 2, 20)

    // Define turn costs
    turnCosts := map[Turn]int{
        {From: 0, Via: 1, To: 2}: 3,  // Turn at node 1 costs 3
    }

    router := NewRouter(graph, turnCosts)
    path, cost := router.ShortestPath(0, 2)

    fmt.Printf("Path: %v, Cost: %d\n", path, cost)
}
```

### Real-World Example

```go
// City routing with turn penalties
graph := LoadCityMap("city.json")

turnPenalties := TurnPenalties{
    LeftTurn:  5,   // 5 seconds
    RightTurn: 2,   // 2 seconds
    UTurn:     15,  // 15 seconds
    Straight:  0,   // 0 seconds
}

router := NewRouterWithPenalties(graph, turnPenalties)
route := router.FindRoute(startAddress, endAddress)
```

## 📊 Complexity Analysis

| Operation               | Time Complexity | Space Complexity |
| :---------------------- | :-------------- | :--------------- |
| **Dijkstra (standard)** | $O(E \log V)$   | $O(V)$           |
| **With turn penalties** | $O(E^2 \log E)$ | $O(E)$           |

Where:

- $V$ = number of nodes
- $E$ = number of edges

The increase is because we effectively create a node for each edge.
