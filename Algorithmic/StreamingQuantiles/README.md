# Streaming Quantiles

A Go implementation of the Greenwald-Khanna algorithm for computing approximate quantiles over a data stream.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Greenwald-Khanna (GK)** is a space-efficient algorithm for computing $\epsilon$-approximate quantiles.
- It maintains a summary of tuples $(v, g, \Delta)$.
- **$v$**: Value of the sample.
- **$g$**: Gap (difference between min rank of this sample and min rank of previous sample).
- **$\Delta$**: Error bound (max rank - min rank).
- The summary allows answering quantile queries with a guaranteed error bound of $\epsilon N$.

## 💻 Installation

```bash
cd Algorithmic/StreamingQuantiles
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "init", "epsilon": 0.1},
  {"type": "insert", "value": 10},
  {"type": "insert", "value": 20},
  {"type": "insert", "value": 15},
  {"type": "query", "phi": 0.5}
]
```

**Output:**
```json
[
  {"result": "initialized"},
  {"result": "inserted"},
  {"result": "inserted"},
  {"result": "inserted"},
  {"result": 15}
]
```

## 📊 Complexity Analysis

| Metric | Complexity |
| :--- | :--- |
| **Space** | $O(\frac{1}{\epsilon} \log (\epsilon N))$ |
| **Insert Time** | $O(\log S)$ (where $S$ is summary size) |
| **Query Time** | $O(S)$ |

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
