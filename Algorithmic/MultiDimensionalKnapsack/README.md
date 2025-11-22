# Multi-dimensional Knapsack Solver

Solves the multi-dimensional knapsack problem where items have multiple resource constraints.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Multi-dimensional knapsack** extends the classic knapsack problem to multiple resource constraints.

### Problem Definition
- Items have value and weights in multiple dimensions (e.g., weight, volume, cost)
- Multiple capacity constraints (e.g., max weight AND max volume)
- Goal: Maximize value while respecting all constraints

### Example
Packing a suitcase:
- Constraint 1: Max weight = 50kg
- Constraint 2: Max volume = 100L
- Each item has weight, volume, and value

### Solution Approaches
1. **Dynamic Programming**: Extend state space to multiple dimensions
2. **Branch and Bound**: For large instances
3. **Greedy Heuristics**: Fast approximations

## 💻 Installation

```bash
go build ./main.go
go test
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "multidimensionalknapsack"
)

func main() {
    // Items: [value, weight, volume]
    items := []Item{
        {Value: 60, Weights: []int{10, 20}},
        {Value: 100, Weights: []int{20, 30}},
        {Value: 120, Weights: []int{30, 40}},
    }
    
    // Capacities: [max_weight, max_volume]
    capacities := []int{50, 60}
    
    solver := NewSolver(items, capacities)
    maxValue, selected := solver.Solve()
    
    fmt.Printf("Max value: %d\n", maxValue)
    fmt.Printf("Selected items: %v\n", selected)
}
```

## 📊 Complexity Analysis

| Approach | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **DP (d dimensions)** | $O(n \prod_{i=1}^{d} W_i)$ | $O(\prod_{i=1}^{d} W_i)$ |
| **Branch & Bound** | Exponential (pruned) | $O(n)$ |

Where:
- $n$ = number of items
- $d$ = number of dimensions
- $W_i$ = capacity in dimension $i$
