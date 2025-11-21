# Approximate String Matching (Levenshtein Distance)

This project implements algorithms for approximate string matching, primarily focusing on **Levenshtein Distance** and efficient data structures for fuzzy search like **BK-Trees** and **N-gram Indices**.

![Levenshtein Distance Visualization](levenshtein_viz.gif)

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Levenshtein Distance
The Levenshtein distance between two strings is the minimum number of single-character edits (insertions, deletions, or substitutions) required to change one word into the other.

It is calculated using Dynamic Programming:
$$D(i, j) = \min \begin{cases} D(i-1, j) + 1 \\ D(i, j-1) + 1 \\ D(i-1, j-1) + (1 \text{ if } s[i] \neq t[j] \text{ else } 0) \end{cases}$$

### BK-Tree (Burkhard-Keller Tree)
A BK-Tree is a tree data structure adapted for metric spaces. It allows for faster fuzzy searching by pruning branches that cannot possibly contain a match, relying on the **Triangle Inequality**:
$$|dist(A, B) - dist(B, C)| \le dist(A, C) \le dist(A, B) + dist(B, C)$$

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Basic Distance Calculation

```python
from approximate_string_matching import levenshtein_distance

dist = levenshtein_distance("kitten", "sitting")
print(f"Distance: {dist}")  # Output: 3
```

### Fuzzy Search with BK-Tree

```python
from approximate_string_matching import BKTree

words = ["apple", "apply", "ape", "banana", "cherry"]
tree = BKTree()
tree.build(words)

# Find words within distance 2 of "app"
matches = tree.search("app", max_distance=2)
print(matches)
# Output: [(1, 'ape'), (2, 'apple')]
```

## 📊 Complexity Analysis

| Algorithm | Time Complexity | Space Complexity | Notes |
| :--- | :--- | :--- | :--- |
| **Levenshtein** | $O(m \cdot n)$ | $O(\min(m, n))$ | Optimized to use only two rows. |
| **BK-Tree Build** | $O(N \log N)$ | $O(N)$ | Average case. |
| **BK-Tree Search** | $O(N)$ (Worst) | $O(N)$ | In practice, prunes significant search space. |

## 🎬 Demos

### Generating the Animation
To generate the DP table visualization:

```bash
manim -pql visualize_levenshtein.py LevenshteinDemo
```
