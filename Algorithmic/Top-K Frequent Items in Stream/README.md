# Top-K Frequent Items (Heavy Hitters)

Implementations of **Misra-Gries** and **Space-Saving** algorithms for finding frequent items (heavy hitters) in a data stream using bounded memory.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

### Problem Framing

Given a stream of items of length **N**, we want to find items that occur more than **N / k** times while using only **O(k)** memory. The algorithms maintain a compact summary of candidate items plus their approximate counts.

### Misra-Gries (Counter-Based Elimination)

Misra-Gries keeps at most **k − 1** counters:

1. If the incoming item already has a counter, increment it.
2. If there is an empty counter slot, add the item with count 1.
3. If the counters are full and the item is new, decrement **all** counters by 1 and remove any that drop to 0.

This step effectively discards a batch of **k** distinct items, which is safe because any true heavy hitter still has enough occurrences to survive repeated decrements.

### Space-Saving (Replace-Min Heuristic)

Space-Saving keeps **k** counters:

1. If the item is present, increment its count.
2. Otherwise, replace the current minimum-count item with the new item and set its count to **min + 1**. The previous minimum becomes the *error* for the new entry.

This overestimates counts but never underestimates the true frequency, making it practical for approximate top-k reporting.

### Ideal Example Test Case (Exercises Edge Cases)

**Stream** (N = 16), **k = 4** (Misra-Gries has 3 counters, threshold N/k = 4):

```
A, B, C, A, D, B, E, A, B, C, A, B, F, A, B, G
```

True frequencies:
- A = 5, B = 5 (heavy hitters: > 4)
- C = 2 (below threshold)
- D, E, F, G = 1 (noise)

This stream forces:
- **Counter fills** (A, B, C)
- **Full-table decrements** (when D/E/F/G appear)
- **Reintroductions** (A/B appear after decrements)
- **Near-threshold item** (C appears but never exceeds N/k)

#### Misra-Gries Step-by-Step

Counters shown as `{item: count}` with at most 3 entries:

1. A → `{A:1}`
2. B → `{A:1, B:1}`
3. C → `{A:1, B:1, C:1}` (full)
4. A → `{A:2, B:1, C:1}`
5. D (new, full) → decrement all → `{A:1, B:0, C:0}` → remove zeros → `{A:1}`
6. B → `{A:1, B:1}`
7. E → `{A:1, B:1, E:1}` (full)
8. A → `{A:2, B:1, E:1}`
9. B → `{A:2, B:2, E:1}`
10. C (new, full) → decrement all → `{A:1, B:1, E:0}` → remove zeros → `{A:1, B:1}`
11. A → `{A:2, B:1}`
12. B → `{A:2, B:2}`
13. F → `{A:2, B:2, F:1}`
14. A → `{A:3, B:2, F:1}`
15. B → `{A:3, B:3, F:1}`
16. G (new, full) → decrement all → `{A:2, B:2, F:0}` → remove zeros → `{A:2, B:2}`

**Result:** Candidates are A and B. They survived multiple decrements, which is the core signal that they appear more than N/k times.

#### Space-Saving Step-by-Step (k = 4)

Counters shown as `{item: count}` with 4 slots. When full and a new item arrives, the minimum count is replaced.

1. A → `{A:1}`
2. B → `{A:1, B:1}`
3. C → `{A:1, B:1, C:1}`
4. A → `{A:2, B:1, C:1}`
5. D (new) → `{A:2, B:1, C:1, D:1}`
6. B → `{A:2, B:2, C:1, D:1}`
7. E (new, full) → min=1, replace one of {C,D} → `{A:2, B:2, E:2, D:1}`
8. A → `{A:3, B:2, E:2, D:1}`
9. B → `{A:3, B:3, E:2, D:1}`
10. C (new, full) → min=1 (D), replace → `{A:3, B:3, E:2, C:2}`
11. A → `{A:4, B:3, E:2, C:2}`
12. B → `{A:4, B:4, E:2, C:2}`
13. F (new, full) → min=2 (E/C), replace → `{A:4, B:4, F:3, C:2}`
14. A → `{A:5, B:4, F:3, C:2}`
15. B → `{A:5, B:5, F:3, C:2}`
16. G (new, full) → min=2 (C), replace → `{A:5, B:5, F:3, G:3}`

**Result:** A and B end with the highest counts. Some noise items temporarily appear but cannot overtake true heavy hitters.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  Install dependencies (if any) from the project root.

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
