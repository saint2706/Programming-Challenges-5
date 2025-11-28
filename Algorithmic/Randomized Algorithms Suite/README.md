# Randomized Algorithms Suite

Implementations of **Skip Lists** and **Treaps**, two randomized data structures that provide balanced tree-like performance ($O(\log N)$) with simpler implementation logic than AVL or Red-Black trees.

![Skip List Visualization](skip_list_viz.gif)

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Skip List

A Skip List is a probabilistic alternative to a balanced binary tree. It consists of multiple layers of linked lists.

- **Bottom Layer**: Contains all elements.
- **Higher Layers**: Each element promotes to the next layer with probability $p$ (usually $0.5$).
- **Search**: Starts at the top layer, moving right until the next node is greater than the target, then drops down a layer.

### Treap

A Treap is a binary search tree that assigns a random **priority** to each node.

- **BST Property**: Maintained on the keys (for searching).
- **Heap Property**: Maintained on the priorities (for balancing).
- Nodes are rotated during insertion/deletion to satisfy the heap property, which keeps the tree balanced with high probability.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Skip List

```python
from skiplist import SkipList

sl = SkipList()
sl.insert("apple", 10)
sl.insert("banana", 20)

print(sl.search("apple"))  # 10
sl.delete("apple")
print(sl.search("apple"))  # None
```

### Treap

```python
from treap import Treap

t = Treap()
t.insert("apple", 10)
t.insert("banana", 20)

print(t.search("banana"))  # 20
t.delete("banana")
```

## 📊 Complexity Analysis

| Structure     | Search (Avg) | Insert (Avg) | Delete (Avg) | Space (Avg) |
| :------------ | :----------- | :----------- | :----------- | :---------- |
| **Skip List** | $O(\log N)$  | $O(\log N)$  | $O(\log N)$  | $O(N)$      |
| **Treap**     | $O(\log N)$  | $O(\log N)$  | $O(\log N)$  | $O(N)$      |

_Worst case is $O(N)$ for both, but the probability of this occurring is exponentially small._

## 🎬 Demos

### Generating the Animation

To generate the Skip List search visualization:

```bash
manim -pql visualize_randomized.py SkipListDemo
```
