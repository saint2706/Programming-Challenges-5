# Pattern Mining in Sequences

Algorithms for discovering frequent sequential patterns in sequence databases using GSP and PrefixSpan algorithms.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Sequential pattern mining** finds frequent subsequences in a sequence database.

### Problem Definition

Given:

- Database of sequences (e.g., customer purchase histories)
- Minimum support threshold

Find: All subsequences that appear in at least `min_support` sequences

**Example**:

```
Database:
  Seq1: <{a, b}, {c}, {f, g}>
  Seq2: <{a, d}, {c}, {b, g}>
  Seq3: <{a}, {b, f}, {c, g}>

Frequent patterns (min_support=2):
  <{a}, {c}>
  <{a}, {g}>
  <{b}, {c}>
```

### Algorithms

#### 1. GSP (Generalized Sequential Pattern)

- **Apriori-like**: Generate-and-test approach
- Generate candidate patterns of length k+1 from frequent patterns of length k
- Count support by scanning database

#### 2. PrefixSpan (Prefix-Projected Sequential Pattern Mining)

- **Pattern growth**: Divide-and-conquer
- Build patterns by growing prefixes
- Use projected databases to avoid repeated scanning

**PrefixSpan is generally faster** as it avoids candidate generation.

## 💻 Installation

```bash
go build ./main.go
go test
```

## 🚀 Usage

### Using GSP

```go
package main

import (
    "fmt"
    "sequencepatternmining"
)

func main() {
    sequences := [][]string{
        {"A", "B", "C"},
        {"A", "C", "B"},
        {"A", "B", "D"},
        {"B", "C", "D"},
    }

    minSupport := 0.5  // 50% support

    gsp := sequencepatternmining.NewGSP(minSupport)
    patterns := gsp.Mine(sequences)

    for _, pattern := range patterns {
        fmt.Printf("Pattern: %v, Support: %.2f\n",
            pattern.Sequence, pattern.Support)
    }
}
```

### Using PrefixSpan

```go
prefixSpan := sequencepatternmining.NewPrefixSpan(minSupport)
patterns := prefixSpan.Mine(sequences)
```

## 📊 Complexity Analysis

| Algorithm      | Time Complexity          | Space Complexity |
| :------------- | :----------------------- | :--------------- |
| **GSP**        | $O(n \cdot k \cdot 2^m)$ | $O(2^m)$         |
| **PrefixSpan** | $O(n \cdot m^2)$         | $O(n \cdot m)$   |

Where:

- $n$ = number of sequences
- $m$ = average sequence length
- $k$ = number of iterations

PrefixSpan is typically much faster in practice.
