# Suffix Automaton Toolkit

A Go implementation of a Suffix Automaton (DAWG) for efficient string processing.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

A **Suffix Automaton** (Directed Acyclic Word Graph) is a compact representation of all substrings of a string.
- It has the minimum number of states among all deterministic automata accepting the suffixes of the string.
- It can be built online in linear time.

### Applications
- **Substring Check**: $O(|pattern|)$
- **Count Distinct Substrings**: $O(|string|)$ (traversal or sum of lengths)
- **Longest Common Substring**: $O(|S1| + |S2|)$

## 💻 Installation

```bash
cd Algorithmic/SuffixAutomaton
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "build", "value": "banana"},
  {"type": "check", "pattern": "ana"},
  {"type": "check", "pattern": "apple"},
  {"type": "distinct"},
  {"type": "lcs", "other": "bandana"}
]
```

**Output:**
```json
[
  {"result": "built"},
  {"result": true},
  {"result": false},
  {"result": 15},
  {"result": "ana"}
]
```
*(Note: LCS might return any valid LCS of maximum length)*

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Build** | $O(N)$ | $O(N \cdot \Sigma)$ |
| **Check Substring** | $O(P)$ | $O(1)$ |
| **Distinct Substrings** | $O(N)$ | $O(1)$ |
| **LCS** | $O(M)$ | $O(1)$ |

Where $N$ is the length of the indexed string, $P$ is pattern length, $M$ is the other string length, and $\Sigma$ is alphabet size.
