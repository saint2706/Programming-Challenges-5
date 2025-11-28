# Map Label Placement

## Theory

This challenge involves placing labels for points on a map such that they do not overlap with each other or the map boundaries, while optimizing for preferred positions (e.g., typically top-right is preferred). This is an NP-Hard problem (specifically, the variation maximizing number of placed labels is equivalent to Maximum Independent Set on rectangles).

We use **Simulated Annealing**, a meta-heuristic, to find a near-optimal solution.

1.  **State:** The configuration of positions for all labels. Each label has 4 candidate positions relative to its point (Top-Right, Top-Left, Bottom-Right, Bottom-Left).
2.  **Energy Function:** $E = \sum (w_{overlap} \times \text{overlaps}) + \sum (w_{bound} \times \text{OOB}) + \sum (w_{pos} \times \text{preference})$.
3.  **Annealing:** We start with a high "temperature". In each step, we perturb the state (move a random label). If the energy decreases, we accept. If it increases, we accept with probability $e^{-\Delta E / T}$. We slowly cool down $T$.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

This generates a `map_labels.png` visualization.

## Complexity Analysis

- **Energy Calculation:** $O(N^2)$ to check all pairs for overlap.
- **One Step:** $O(N)$ (since we only change one label, we only need to re-check its overlaps with others, not all pairs).
- **Total:** $O(K \times N)$ where $K$ is number of iterations.

## Demos

See `map_labels.png`.
