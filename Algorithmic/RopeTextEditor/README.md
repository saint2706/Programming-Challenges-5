# Rope-based Text Editor Core

A Go implementation of a Rope data structure for efficient text editing.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

A **Rope** is a tree-based data structure where each leaf node contains a short string. Internal nodes store the "weight" (length) of their left subtree. This allows for efficient operations on large strings.

### Operations
- **Concat**: Join two ropes. $O(1)$ (ignoring rebalancing).
- **Split**: Split a rope into two at index $i$. $O(\log n)$.
- **Insert**: Split at $i$, concat with new string, concat with remainder. $O(\log n)$.
- **Delete**: Split at start, split remainder at end, concat the two ends. $O(\log n)$.
- **Index**: Traverse the tree using weights. $O(\log n)$.

## 💻 Installation

```bash
cd Algorithmic/RopeTextEditor
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "new", "value": "Hello"},
  {"type": "insert", "index": 5, "value": " World"},
  {"type": "print"}
]
```

**Output:**
```json
[
  {"result": "created"},
  {"result": "inserted"},
  {"result": "Hello World"}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Index** | $O(\log n)$ |
| **Concat** | $O(1)$ |
| **Split** | $O(\log n)$ |
| **Insert** | $O(\log n)$ |
| **Delete** | $O(\log n)$ |

*Note: This naive implementation does not auto-balance the tree, so worst-case performance can degrade to $O(n)$ if constructed linearly. Production ropes (e.g., in text editors) use rebalancing (AVL/Red-Black rules).*

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
