# Generic DP Visualizer (Knapsack)

A visualization of the **0/1 Knapsack Problem** solved using Dynamic Programming.

![DP Visualization](dp_generic_viz.gif)

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### The Problem
Given a set of items, each with a weight and a value, determine the number of each item to include in a collection so that the total weight is less than or equal to a given limit and the total value is as large as possible.

### The Recurrence
Let $dp[i][w]$ be the maximum value that can be obtained using a subset of the first $i$ items with maximum capacity $w$.

$$dp[i][w] = \max(dp[i-1][w], \text{value}[i] + dp[i-1][w-\text{weight}[i]])$$
*(if weight[i] <= w)*

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

This project is primarily a visualization script.

### Generating the Animation
To generate the DP table filling animation:

```bash
manim -pql visualize_dp_generic.py GenericDPDemo
```

## 📊 Complexity Analysis

| Algorithm | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Knapsack DP** | $O(N \cdot W)$ | $O(N \cdot W)$ |

Where $N$ is the number of items and $W$ is the capacity.
*Note: This is pseudo-polynomial time.*

## 🎬 Demos

See the GIF above for the generated animation.
