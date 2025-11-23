# Auto-Completion with Language Model Prior

## Theory
This challenge implements a hybrid auto-completion engine that improves upon standard Trie-based lookups by incorporating context from a Language Model (N-gram).

1.  **Trie (Prefix Tree):** Efficiently finds all words starting with a given prefix. Each node stores the frequency of the word to rank common words higher.
2.  **Language Model (N-gram):** Predicts the probability of a word given the previous $N-1$ words. $P(w_i | w_{i-1}, \dots, w_{i-N+1})$.
    *   For this implementation, we use a simple **Bigram (N=2)** or **Trigram (N=3)** model.
    *   The ranking score combines the global frequency (unigram probability) and the context-dependent probability.

## Installation
No external dependencies are required.

```bash
# Optional: create a virtual env
python3 -m venv venv
source venv/bin/activate
```

## Usage
Run the interactive CLI:

```bash
python main.py
```

Example session:
```
> the qu
Suggestions: ['quick']
> artificial in
Suggestions: ['intelligence']
```

## Complexity Analysis
*   **Training:** $O(L)$ where $L$ is the total length of the corpus (inserting into Trie and updating N-gram counts).
*   **Lookup (Prefix Search):** $O(P)$ where $P$ is the length of the prefix.
*   **Candidate Retrieval:** $O(C \times W)$ where $C$ is the number of candidates and $W$ is average word length (DFS traversal).
*   **Ranking:** $O(C \log C)$ to sort or heapify candidates.

## Demos
(Screenshots or logs would go here)
