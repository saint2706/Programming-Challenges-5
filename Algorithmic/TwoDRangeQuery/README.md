# 2D Range Query Library

A Go implementation of a 2D Fenwick Tree (Binary Indexed Tree) for efficient range sum queries and point updates.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

A **2D Fenwick Tree** extends the 1D concept to two dimensions. It allows calculating prefix sums in a 2D grid efficiently.

### Operations
- **Update(r, c, delta)**: Adds `delta` to the value at `(r, c)`.
- **Query(r1, c1, r2, c2)**: Returns the sum of elements in the rectangle defined by top-left `(r1, c1)` and bottom-right `(r2, c2)`.
  - Utilizes the Principle of Inclusion-Exclusion:
    $Sum(r1, c1, r2, c2) = Prefix(r2, c2) - Prefix(r1-1, c2) - Prefix(r2, c1-1) + Prefix(r1-1, c1-1)$

## 💻 Installation

```bash
cd Algorithmic/TwoDRangeQuery
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "init", "rows": 4, "cols": 4},
  {"type": "update", "r": 1, "c": 1, "val": 5},
  {"type": "update", "r": 2, "c": 2, "val": 10},
  {"type": "query", "r1": 0, "c1": 0, "r2": 3, "c2": 3},
  {"type": "query", "r1": 1, "c1": 1, "r2": 1, "c2": 1}
]
```

**Output:**
```json
[
  {"result": "initialized"},
  {"result": "updated"},
  {"result": "updated"},
  {"result": 15},
  {"result": 5}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Update** | $O(\log N \cdot \log M)$ | $O(N \cdot M)$ |
| **Query** | $O(\log N \cdot \log M)$ | $O(N \cdot M)$ |

Where $N$ is rows and $M$ is columns.
