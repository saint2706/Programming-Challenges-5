# Edit Distance with Custom Costs

A dynamic programming solution for computing edit distance (Levenshtein distance) with customizable operation costs for insertions, deletions, and substitutions.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Edit distance** measures how different two strings are by counting the minimum number of operations needed to transform one string into another.

### Standard Operations

- **Insert**: Add a character
- **Delete**: Remove a character
- **Substitute**: Replace one character with another

### Dynamic Programming Approach

Define $dp[i][j]$ as the minimum cost to transform the first $i$ characters of string A into the first $j$ characters of string B.

**Recurrence**:

$$
dp[i][j] = \min \begin{cases}
dp[i-1][j] + \text{cost}_{\text{del}} \\
dp[i][j-1] + \text{cost}_{\text{ins}} \\
dp[i-1][j-1] + \text{cost}_{\text{sub}} \text{ if } A[i] \neq B[j] \\
dp[i-1][j-1] \text{ if } A[i] = B[j]
\end{cases}
$$

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

### Basic Usage

```rust
use edit_distance_with_custom_costs::EditDistance;

// Standard edit distance (all costs = 1)
let dist = EditDistance::compute("kitten", "sitting");
println!("Distance: {}", dist);  // Output: 3

// Custom costs
let ed = EditDistance::new(1, 1, 2);  // insert, delete, substitute
let dist = ed.compute_with_costs("hello", "help");
```

## 📊 Complexity Analysis

| Operation   | Time    | Space   |
| :---------- | :------ | :------ |
| **Compute** | $O(mn)$ | $O(mn)$ |

Where $m$ and $n$ are the lengths of the two strings.
