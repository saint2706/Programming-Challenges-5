# Graph Isomorphism Checker (Heuristic)

A Go implementation of the **Weisfeiler-Lehman (WL)** test for graph isomorphism.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

The **Graph Isomorphism Problem** asks whether two graphs are structurally identical. No polynomial-time algorithm is known for the general case.
The **Weisfeiler-Lehman (WL) Test** (specifically the 1-WL or Color Refinement algorithm) is a powerful heuristic.
1. Assign initial colors to nodes (e.g., based on degree).
2. Iteratively refine colors: New color of node $v$ depends on its current color and the multiset of colors of its neighbors.
3. If the multisets of final colors of two graphs differ, they are **not** isomorphic.
4. If they match, they are **likely** isomorphic (WL distinguishes almost all graphs).

## 💻 Installation

```bash
cd Algorithmic/GraphIsomorphism
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {
    "type": "check",
    "graph1": {"nodes": 3, "edges": [{"u":0,"v":1}, {"u":1,"v":2}]},
    "graph2": {"nodes": 3, "edges": [{"u":1,"v":0}, {"u":0,"v":2}]}
  }
]
```

**Output:**
```json
[
  {"result": true}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **WL Iteration** | $O(M)$ where $M$ is edges |
| **Total** | $O(K \cdot M)$ where $K$ is iterations |
