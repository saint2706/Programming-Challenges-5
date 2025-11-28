# On-Disk B-Tree Index

A Go implementation of a B-Tree data structure designed for on-disk storage.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**B-Tree** is a self-balancing tree data structure that maintains sorted data and allows searches, sequential access, insertions, and deletions in logarithmic time. It is optimized for systems that read and write large blocks of data (like disks).

### Structure
- **Nodes (Pages)** are fixed-size blocks (e.g., 4KB).
- **Internal Nodes**: Contain keys and pointers to children.
- **Leaf Nodes**: Contain keys and values (or pointers to records).
- **Order $m$**: A node has at most $m$ children and $m-1$ keys.
- **Balancing**: All leaf nodes are at the same depth.

### Operations
- **Search**: Traverse from root to leaf. $O(\log_m N)$.
- **Insert**: Insert into leaf. If full, split node and promote median key to parent. $O(\log_m N)$ I/O operations.

## 💻 Installation

```bash
cd Algorithmic/OnDiskBTree
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "insert", "key": 10, "value": 100},
  {"type": "insert", "key": 20, "value": 200},
  {"type": "search", "key": 10}
]
```

**Output:**
```json
[
  {"result": "inserted"},
  {"result": "inserted"},
  {"result": 100}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity (I/O) | Space Complexity |
| :--- | :--- | :--- |
| **Search** | $O(\log_m N)$ | $O(N)$ |
| **Insert** | $O(\log_m N)$ | $O(N)$ |

Where $N$ is the number of keys and $m$ is the order (branching factor).

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
