# Autocomplete Engine (Trie)

An efficient Autocomplete Engine implemented using a **Trie** (Prefix Tree). It supports fast prefix lookups, word frequency tracking, and JSON persistence.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

### Core Idea

A **Trie** stores words by sharing common prefixes. Each node represents a character and marks whether the path so far forms a complete word. The Autocomplete Engine extends this by storing frequency counts on terminal nodes so the top-k suggestions can be ranked by popularity.

### Ideal Example Test Case (Exercises Edge Cases)

**Insert sequence (word → frequency):**

1. `app → 5`
2. `apple → 10`
3. `application → 8`
4. `apply → 8` (tie frequency)
5. `apt → 3` (shorter word diverging after `ap`)
6. `app → +2` (frequency update on existing word)
7. `banana → 2` (different prefix)

**Queries:**

- `top_k("app", k=3)` (prefix equals full word, includes ties)
- `top_k("ap", k=10)` (k exceeds number of matches)
- `top_k("xyz", k=2)` (prefix not present)

This case covers:
- **Prefix as a full word** (`app`)
- **Frequency updates** (re-inserting `app`)
- **Tie-breaking** (`application` vs `apply`)
- **Prefix breadth** (`ap` collects multiple branches)
- **Empty result** (`xyz`)

### Step-by-Step Walkthrough

#### 1) Inserting `app → 5`
- Create nodes: `a → p → p`.
- Mark the last `p` as a word end, set frequency to 5.

#### 2) Inserting `apple → 10`
- Reuse `a → p → p`.
- Create `l → e` nodes.
- Mark `e` as word end with frequency 10.

#### 3) Inserting `application → 8`
- Reuse `a → p → p → l`.
- Create `i → c → a → t → i → o → n`.
- Mark `n` with frequency 8.

#### 4) Inserting `apply → 8`
- Reuse `a → p → p → l`.
- Create `y` node, mark as word end with frequency 8.
- Tie frequency with `application` will be resolved lexicographically.

#### 5) Inserting `apt → 3`
- Reuse `a → p`.
- Create `t` node, mark as word end with frequency 3.

#### 6) Updating `app → +2`
- Traverse to the `app` terminal node.
- Increase frequency from 5 to 7 (now higher than `apt`).

#### 7) Inserting `banana → 2`
- Create a separate branch under `b`.
- This ensures non-matching prefixes do not pollute `ap` suggestions.

### Query Evaluation

#### `top_k("app", k=3)`
1. Traverse prefix `app` to the subtree root.
2. Collect all terminal nodes below:
   - `app` (7), `apple` (10), `application` (8), `apply` (8).
3. Sort by frequency descending, then lexicographically for ties.
4. Output: `apple` (10), `application` (8), `apply` (8).

#### `top_k("ap", k=10)`
1. Prefix `ap` includes `app`, `apple`, `application`, `apply`, `apt`.
2. Only 5 results exist, so return all 5 in ranked order.

#### `top_k("xyz", k=2)`
1. Prefix path not found → empty list.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  Install dependencies (if any) from the project root.

## 🚀 Usage

### Basic Usage

```python
from trie import AutocompleteEngine

engine = AutocompleteEngine()

# Insert words with frequencies
engine.insert("apple", frequency=10)
engine.insert("app", frequency=5)
engine.insert("application", frequency=8)
engine.insert("banana", frequency=2)

# Get top 2 suggestions for "app"
suggestions = engine.top_k("app", k=2)
print(suggestions)
# Output: ['apple', 'application'] (sorted by frequency)
```

### Persistence

```python
# Save to disk
engine.to_json("trie_data.json")

# Load from disk
loaded_engine = AutocompleteEngine.from_json("trie_data.json")
```

## 📊 Complexity Analysis

Let $L$ be the length of the word/prefix.

| Operation         | Time Complexity   | Space Complexity               |
| :---------------- | :---------------- | :----------------------------- |
| **Insert**        | $O(L)$            | $O(L)$ (worst case, new nodes) |
| **Search/Prefix** | $O(L)$            | $O(1)$                         |
| **Top-K**         | $O(L + N \log N)$ | $O(N)$                         |

_Note: Top-K involves traversing the subtree (size $N$) and sorting the results._
