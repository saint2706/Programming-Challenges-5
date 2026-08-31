# Top-K Frequent Items (Heavy Hitters)

Implementations of **Misra-Gries** and **Space-Saving** algorithms for finding frequent items (heavy hitters) in a data stream using bounded memory.

![Misra-Gries Visualization](misra_gries_viz.gif)

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Misra-Gries Algorithm

Used to find items that appear more than $N/k$ times in a stream of length $N$.

- Maintains $k-1$ counters.
- If a new item matches a counter, increment it.
- If not matching and space exists, add a new counter with count 1.
- If counters are full, decrement **all** counters by 1 (effectively discarding $k$ distinct items at once).

### Space-Saving Algorithm

Similar goal but provides better estimates in practice.

- Maintains $k$ counters.
- If a new item matches, increment.
- If counters are full, **replace the item with the minimum count**, incrementing that count and tracking the "error" (the count of the evicted item).
- Guarantees that the estimated count is at least the real count (overestimation).

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Misra-Gries

```python
from misra_gries import MisraGriesCounter

# Find items appearing > 1/3 of the time (k=3)
mg = MisraGriesCounter(k=3)
mg.bulk_update(["A", "B", "A", "C", "A", "D"])

print(mg.heavy_hitters())
# Output: [FrequentItem(item='A', estimate=2, error=0)]
```

### Space-Saving

```python
from misra_gries import SpaceSavingCounter

ss = SpaceSavingCounter(k=3)
ss.bulk_update(["A", "B", "A", "C", "A", "D"])

print(ss.heavy_hitters())
```

## 📊 Complexity Analysis

| Algorithm        | Space Complexity | Time Complexity (per update)              |
| :--------------- | :--------------- | :---------------------------------------- |
| **Misra-Gries**  | $O(k)$           | $O(1)$ (Amortized) or $O(k)$ (Worst case) |
| **Space-Saving** | $O(k)$           | $O(1)$ (using proper data structures)     |

## 🏆 Optimal Solution

This directory also contains a research-backed analysis of the _optimal_ solution to
this challenge, the alternatives that lose and why, and a measured
implementation of O(1) worst-case Space-Saving, mergeable Misra-Gries, and HeavyKeeper.

- **[OPTIMAL.md](OPTIMAL.md)** — the analysis, benchmarks and references.
- **[`optimal_topk.py`](optimal_topk.py)** — the implementation. Run it directly to
  reproduce the benchmarks:

  ```bash
  python optimal_topk.py
  ```

## 🎬 Demos

### Generating the Animation

To generate the Misra-Gries visualization:

```bash
manim -pql visualize_misra_gries.py MisraGriesDemo
```
