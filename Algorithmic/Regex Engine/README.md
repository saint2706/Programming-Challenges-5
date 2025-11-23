# Regex Engine

## Theory
This challenge implements a basic Regular Expression engine using **Thompson's Construction** to convert the regex into a Non-Deterministic Finite Automaton (NFA).

1.  **Parsing:** Convert infix regex (e.g., `a(b|c)*`) to postfix (e.g., `abc|*.`) using the Shunting-Yard algorithm. Explicit concatenation operators are inserted during preprocessing.
2.  **NFA Construction:**
    *   **Literal `a`:** Start state $\to^a$ End state.
    *   **Concatenation `AB`:** Join End of A to Start of B with $\epsilon$.
    *   **Union `A|B`:** New Start splits to A and B with $\epsilon$. A and B join to New End with $\epsilon$.
    *   **Closure `A*`:** New Start goes to A and New End. A loops back to itself and goes to New End.
3.  **Simulation:** Simulating an NFA involves maintaining a *set* of active states. For each input character, we transition all active states and then compute the $\epsilon$-closure (all states reachable by $\epsilon$-transitions).

## Installation
No external dependencies.

## Usage
```bash
python main.py
```

## Complexity Analysis
*   **Compilation:** $O(|P|)$ where $|P|$ is pattern length.
*   **Matching:** $O(|P| \times |S|)$ where $|S|$ is string length. The number of active states is at most linear in $|P|$.
*   **Space:** $O(|P|)$ to store the NFA.

## Demos
Run `main.py` to see matches for various patterns.
