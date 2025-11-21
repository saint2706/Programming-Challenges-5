# Advanced Interval Scheduler (Weighted)

This project implements the **Weighted Interval Scheduling** algorithm using Dynamic Programming. Given a set of intervals, each with a start time, end time, and a weight (value), the goal is to find a subset of non-overlapping intervals that maximizes the total weight.

![Interval Scheduler Visualization](interval_scheduler_viz.gif)
*(Note: Visualization above shows the greedy strategy for the unweighted case, which is a simplified version of the problem)*

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

The Weighted Interval Scheduling problem is solved efficiently using **Dynamic Programming**.

### The Recurrence
Let intervals be sorted by finish time $f_1 \le f_2 \le \dots \le f_n$.
Let $p(j)$ be the largest index $i < j$ such that interval $i$ is compatible with interval $j$ (i.e., $f_i \le s_j$).

Define $OPT(j)$ as the maximum weight of a subset of non-overlapping intervals drawn from $\{1, \dots, j\}$.

The recurrence relation is:
$$OPT(j) = \max(w_j + OPT(p(j)), OPT(j-1))$$

Where:
-   $w_j + OPT(p(j))$ represents **including** interval $j$ (and adding the optimal solution of compatible predecessors).
-   $OPT(j-1)$ represents **excluding** interval $j$ (inheriting the optimal solution from the previous subproblem).

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` if you wish to generate visualizations:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Basic API

```python
from main import AdvancedIntervalScheduler

# Define intervals as (start, end, weight) tuples
intervals = [
    (1, 3, 5),
    (2, 5, 6),
    (4, 6, 5),
    (6, 7, 8)
]

# Initialize scheduler
scheduler = AdvancedIntervalScheduler(intervals)

# Find optimal schedule
max_weight, selected_intervals = scheduler.find_optimal_schedule()

print(f"Maximum Weight: {max_weight}")
for interval in selected_intervals:
    print(interval)
```

## 📊 Complexity Analysis

| Step | Complexity | Description |
| :--- | :--- | :--- |
| **Sorting** | $O(n \log n)$ | Intervals are sorted by end time. |
| **Predecessors** | $O(n \log n)$ | Binary search is performed for each interval to find $p(j)$. |
| **DP Table** | $O(n)$ | Filling the table takes linear time. |
| **Backtracking** | $O(n)$ | Reconstructing the solution takes linear time. |
| **Total Time** | **$O(n \log n)$** | Dominated by sorting and binary search. |
| **Total Space** | **$O(n)$** | To store the intervals, DP table, and $p$ array. |

## 🎬 Demos

### Running the Code Demo
Run the included demo script to see the algorithm handle various test cases and a performance benchmark.

```bash
python demo.py
```

### Generating the Animation
To generate a visualization of the scheduling process (Greedy version for visual simplicity):

```bash
manim -pql visualize_interval_scheduler.py IntervalSchedulingDemo
```
