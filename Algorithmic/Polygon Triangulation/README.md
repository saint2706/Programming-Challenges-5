# Polygon Triangulation

## Theory

Polygon triangulation is the process of decomposing a polygon into a set of triangles. This implementation uses the **Ear Clipping** method.

1.  **Ear:** A vertex of a polygon is an "ear" if the triangle formed by it and its two neighbors lies entirely inside the polygon.
2.  **Algorithm:**
    - Find an ear vertex $V_i$.
    - Add triangle $(V_{i-1}, V_i, V_{i+1})$ to the list.
    - Remove $V_i$ from the polygon.
    - Repeat until only 3 vertices remain (the last triangle).

The implementation assumes a **Simple Polygon** (no self-intersections) defined in **Counter-Clockwise (CCW)** order.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the demo:

```bash
python main.py
```

This will generate `triangulation_demo.png` visualizing the result.

## Complexity Analysis

- **Naive Ear Clipping:** $O(n^2)$. In each step, we iterate through vertices to find an ear. Checking if a vertex is an ear takes $O(n)$ (checking if other points are inside). We remove $n-2$ ears. Total $O(n^3)$ if naive, but optimized to $O(n^2)$ by efficient geometric checks.
- **Optimized:** Can be $O(n \log n)$ or even $O(n)$ with complex data structures, but $O(n^2)$ is standard for ear clipping.

## Demos

See `triangulation_demo.png` after running `main.py`.
