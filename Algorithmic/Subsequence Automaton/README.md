# Subsequence Automaton

## Theory
A Subsequence Automaton (also known as a Directed Acyclic Subsequence Graph if optimized, though here implemented as a transition table) is a data structure built on a string $T$ that allows answering queries of the form "Is $S$ a subsequence of $T$?" efficiently.

Without the automaton, checking if $S$ is a subsequence of $T$ takes $O(|T|)$ greedily. With the automaton, it takes $O(|S|)$, which is independent of the size of the original text $T$.

1.  **Construction:** We compute a table `next[i][c]` which stores the index of the first occurrence of character `c` in $T$ at or after index `i`.
2.  **Query:** To match $S$, we start at index 0. For each character $c$ in $S$, we jump to `next[current_index][c]` and then advance the pointer by 1. If at any point the entry doesn't exist, $S$ is not a subsequence.

## Installation
No external dependencies.

## Usage
```bash
python main.py
```

## Complexity Analysis
*   **Preprocessing:** $O(|T| \times |\Sigma|)$ where $\Sigma$ is the alphabet size. We iterate backwards and maintain the nearest occurrence of each character.
*   **Query:** $O(|S|)$.
*   **Space:** $O(|T| \times |\Sigma|)$.

This is ideal when $|T|$ is large and we have many queries $S$.
