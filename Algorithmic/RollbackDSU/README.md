# Disjoint Set with Rollback

A Disjoint Set Union (Union-Find) data structure that supports rollback operations to undo unions.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Disjoint Set Union (DSU)** maintains a collection of disjoint sets with efficient union and find operations.

### Standard DSU Optimizations
1. **Path compression**: Make trees flat during find
2. **Union by rank**: Attach smaller tree under larger tree

### Rollback Support
To support rollback, we **cannot use path compression** (it loses history). Instead:
- Store history of all union operations
- Rollback by popping from history stack
- Use **union by size** instead of path compression

### Applications
- Online connectivity problems with backtracking
- Temporal graphs (edges added/removed over time)
- Persistent data structures

## 💻 Installation

```bash
go build
go test
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "rollbackdsu"
)

func main() {
    dsu := rollbackdsu.NewDSU(5)
    
    // Initial unions
    dsu.Union(0, 1)
    dsu.Union(2, 3)
    fmt.Println(dsu.Connected(0, 1))  // true
    fmt.Println(dsu.Connected(0, 2))  // false
    
    // Save checkpoint
    checkpoint := dsu.Checkpoint()
    
    // More unions
    dsu.Union(1, 2)
    fmt.Println(dsu.Connected(0, 3))  // true
    
    // Rollback
    dsu.Rollback(checkpoint)
    fmt.Println(dsu.Connected(0, 3))  // false (undone)
}
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Find** | $O(\log n)$ |
| **Union** | $O(\log n)$ |
| **Rollback** | $O(k)$ |

Where:
- $n$ = number of elements
- $k$ = number of operations to rollback

**Note**: Without path compression, find is $O(\log n)$ instead of $O(\alpha(n))$.

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
