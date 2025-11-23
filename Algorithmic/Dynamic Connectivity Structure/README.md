# Dynamic Connectivity Structure

## Theory
This challenge requires a data structure that maintains connectivity information (components) of an undirected graph while edges are inserted and deleted.

For fully dynamic connectivity, the state-of-the-art algorithms (like Holm, de Lichtenberg, Thorup) achieve polylogarithmic amortized time per operation ($O(\log^2 V)$).

This implementation uses a simplified **Spanning Forest with Reconnection** approach:
1.  Maintain a global set of edges ($G$) and a Spanning Forest ($F$).
2.  **Insert(u, v):** If $u, v$ are already connected in $F$, add $(u,v)$ to $G$ as a non-tree edge. Otherwise, add to $F$ (merge trees).
3.  **Delete(u, v):**
    *   If $(u,v)$ is a non-tree edge, just remove from $G$.
    *   If $(u,v)$ is a tree edge, removing it splits a tree $T$ into $T_u$ and $T_v$. We must search for a non-tree edge in $G$ that connects $T_u$ and $T_v$ to reconnect them. This search can be expensive ($O(E)$ worst case) in this naive implementation, but correct.

## Installation
No external dependencies.

## Usage
```bash
python main.py
```

## Complexity Analysis
*   **Query (Connected):** $O(V)$ (BFS/DFS on the spanning tree).
*   **Insert:** $O(V)$ (Connectivity check + constant update).
*   **Delete:** $O(E)$ worst case (scanning edges to reconnect).

*Note: A true $O(\log^2 V)$ implementation requires Euler Tour Trees or Link-Cut Trees with level structures, which significantly exceeds the code size of a typical challenge solution.*

## Demos
Run `main.py` to see edges being added/removed and connectivity preserved via alternative paths.
