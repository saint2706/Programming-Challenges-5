# Suffix Array + LCP

A Go implementation of Suffix Array construction and Kasai's algorithm for the Longest Common Prefix (LCP) array.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Suffix Array**: An integer array providing the starting indices of all suffixes of a string sorted in lexicographical order.
**LCP Array**: An array where `LCP[i]` is the length of the longest common prefix between the suffix at `SA[i]` and `SA[i-1]`.

### Algorithms

- **Construction**: Using prefix doubling ($O(N \log^2 N)$ or $O(N \log N)$).
- **LCP Construction**: Kasai's Algorithm ($O(N)$).

### Applications

- **Pattern Matching**: $O(P \log N)$ using binary search on SA.
- **Distinct Substrings**: $\sum (N - SA[i] - LCP[i])$.

## 💻 Installation

```bash
cd Algorithmic/SuffixArrayLCP
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**

```json
[
  { "type": "sa", "value": "banana" },
  { "type": "lcp", "value": "banana" },
  { "type": "distinct", "value": "banana" }
]
```

**Output:**

```json
[
  { "result": [5, 3, 1, 0, 4, 2] },
  { "result": [0, 1, 3, 0, 0, 2] },
  { "result": 15 }
]
```

## 📊 Complexity Analysis

| Operation        | Time Complexity | Space Complexity |
| :--------------- | :-------------- | :--------------- |
| **Suffix Array** | $O(N \log^2 N)$ | $O(N)$           |
| **LCP Array**    | $O(N)$          | $O(N)$           |
