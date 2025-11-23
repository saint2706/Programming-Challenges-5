# Geometry Engine 2D

A Go implementation of 2D Computational Geometry algorithms.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

### Convex Hull (Monotone Chain)
Finds the smallest convex polygon containing all points.
1. Sort points by X (then Y).
2. Build lower hull by iterating forward.
3. Build upper hull by iterating backward.
4. $O(N \log N)$ due to sorting.

### Point in Polygon (Ray Casting)
Determines if a point is inside a polygon by casting a ray to infinity and counting intersections with edges.
- Odd intersections: Inside.
- Even intersections: Outside.
- $O(N)$ where $N$ is vertices.

### Area (Shoelace Formula)
Calculates area using coordinates.
- $A = \frac{1}{2} | \sum (x_i y_{i+1} - x_{i+1} y_i) |$
- $O(N)$.

## 💻 Installation

```bash
cd Algorithmic/GeometryEngine2D
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "hull", "points": [{"x":0,"y":0}, {"x":2,"y":2}, {"x":0,"y":2}, {"x":2,"y":0}, {"x":1,"y":1}]},
  {"type": "inside", "polygon": [{"x":0,"y":0}, {"x":2,"y":0}, {"x":2,"y":2}, {"x":0,"y":2}], "point": {"x":1,"y":1}},
  {"type": "area", "polygon": [{"x":0,"y":0}, {"x":2,"y":0}, {"x":2,"y":2}, {"x":0,"y":2}]}
]
```

**Output:**
```json
[
  {"result": [{"x":0,"y":0}, {"x":2,"y":0}, {"x":2,"y":2}, {"x":0,"y":2}]},
  {"result": true},
  {"result": 4}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Convex Hull** | $O(N \log N)$ |
| **Point in Polygon** | $O(V)$ |
| **Area** | $O(V)$ |
