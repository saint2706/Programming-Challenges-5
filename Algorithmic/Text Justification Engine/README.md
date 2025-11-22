# Text Justification Engine

A dynamic programming solution for optimally justifying text to a given line width by minimizing raggedness.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Text justification** breaks text into lines to minimize "badness" - the total penalty for whitespace at line ends.

### Problem Definition
Given words $w_1, w_2, ..., w_n$ and line width $W$, arrange words into lines to minimize total cost.

**Cost of a line**: If a line has remaining spaces $s$:
- $\text{cost} = s^3$ (penalizes very ragged lines more)
- Last line: $\text{cost} = 0$ (can be ragged)

### Dynamic Programming
$dp[i]$ = minimum total cost to justify words from $i$ to $n$

**Recurrence**: For each word $i$, try fitting words $i$ through $j$ on one line:
$$dp[i] = \min_{j \geq i} (\text{cost}(i, j) + dp[j+1])$$

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use text_justification_engine::justify;

let text = "The quick brown fox jumps over the lazy dog";
let width = 16;

let justified = justify(text, width);
for line in justified {
    println!("{}", line);
}

// Output:
// The quick brown
// fox jumps over
// the lazy dog
```

## 📊 Complexity Analysis

| Operation | Time | Space |
| :--- | :--- | :--- |
| **Justify** | $O(n^2)$ | $O(n)$ |

Where $n$ is the number of words.
