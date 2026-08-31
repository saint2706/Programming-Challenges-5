# Autocomplete Engine (Trie)

An efficient Autocomplete Engine implemented using a **Trie** (Prefix Tree). It supports fast prefix lookups, word frequency tracking, and JSON persistence.

![Trie Visualization](trie_viz.gif)

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

A **Trie** (pronounced "try") is a tree-based data structure used to efficiently store and retrieve keys in a dataset of strings.

- **Nodes**: Each node represents a character.
- **Edges**: Links between nodes represent the next character in the string.
- **Root**: Represents an empty string.
- **Word Marking**: Some nodes are marked as "end of word" to distinguish complete words from prefixes.

### Why Tries?

- **Prefix Search**: Finding all words starting with "app" is $O(L)$ where $L$ is the prefix length.
- **Space Efficiency**: Common prefixes are stored only once.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

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

## 🏆 Optimal Solution

This directory also contains a research-backed analysis of the _optimal_ solution to
this challenge, the alternatives that lose and why, and a measured
implementation of O(p + k log k) top-k completion.

- **[OPTIMAL.md](OPTIMAL.md)** — the analysis, benchmarks and references.
- **[`optimal_autocomplete.py`](optimal_autocomplete.py)** — the implementation. Run it directly to
  reproduce the benchmarks:

  ```bash
  python optimal_autocomplete.py
  ```

## 🎬 Demos

### Generating the Animation

To generate the Trie construction visualization:

```bash
manim -pql visualize_trie.py TrieDemo
```
