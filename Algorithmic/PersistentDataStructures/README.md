# Persistent Data Structures Kit

A Go implementation of a persistent vector using path copying in a tree structure.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Persistent Data Structures** are data structures that preserve their previous versions when modified. They are effectively immutable.

### Path Copying
When a node in the tree is modified (e.g., `Set(index, value)`), we do not modify the node in place. Instead, we create a copy of the node with the new value. Because the parent points to the old node, we must also copy the parent to point to the new child. This propagates up to the root.
- **Result**: A new root node representing the new version of the structure.
- **Efficiency**: Only the nodes along the path from the root to the leaf are copied. Shared nodes remain untouched.

### Structure
This implementation uses a Tree (conceptually a bit-mapped trie logic simplified to binary or fixed branching) to represent the array.
- **Get**: $O(\log n)$ traversal.
- **Set**: $O(\log n)$ path copy.
- **Append**: $O(\log n)$ insertion (may involve growing the tree height).

## 💻 Installation

```bash
cd Algorithmic/PersistentDataStructures
go build
go test
```

## 🚀 Usage

The `main` program accepts a list of JSON commands from stdin.

**Input Format:**
```json
[
  {"type": "append", "ver": 0, "value": 10},
  {"type": "append", "ver": 1, "value": 20},
  {"type": "set", "ver": 2, "index": 0, "value": 99},
  {"type": "get", "ver": 2, "index": 0},
  {"type": "get", "ver": 3, "index": 0}
]
```
*Note: Version 0 is the initial empty array.*

**Output:**
```json
[
  {"version": 1},
  {"version": 2},
  {"version": 3},
  {"value": 10},
  {"value": 99}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Get** | $O(\log_B n)$ | $O(1)$ |
| **Set** | $O(\log_B n)$ | $O(\log_B n)$ (new nodes) |
| **Append** | $O(\log_B n)$ | $O(\log_B n)$ (new nodes) |

Where $B$ is the branching factor (2 in the binary case, usually 32 in practical implementations).
