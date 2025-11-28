# Clustering Algorithms Suite

A comprehensive suite of clustering algorithms including k-means, k-medoids, and DBSCAN for grouping similar data points.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Clustering** groups data points so that points in the same group are more similar to each other than to those in other groups.

### Algorithms Implemented

#### 1. K-Means
- **Goal**: Partition data into k clusters
- **Method**: Iteratively assign points to nearest centroid and recompute centroids
- **Pros**: Fast, simple
- **Cons**: Sensitive to outliers, requires k to be specified

#### 2. K-Medoids
- **Goal**: Similar to k-means but uses actual data points as centers
- **Method**: Select k representative points (medoids)
- **Pros**: More robust to outliers than k-means
- **Cons**: More expensive computationally

#### 3. DBSCAN (Density-Based Spatial Clustering)
- **Goal**: Find clusters of arbitrary shape based on density
- **Method**: Group points that are closely packed, mark outliers
- **Pros**: No need to specify k, finds arbitrary shapes, handles outliers
- **Cons**: Sensitive to parameters (epsilon, min_points)

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

### K-Means

```rust
use clustering_algorithms_suite::{KMeans, Point};

let points = vec![
    Point::new(vec![1.0, 2.0]),
    Point::new(vec![1.5, 1.8]),
    Point::new(vec![5.0, 8.0]),
    Point::new(vec![8.0, 8.0]),
];

let k = 2;
let kmeans = KMeans::new(k, 100);  // k clusters, max 100 iterations
let clusters = kmeans.fit(&points);

for (i, cluster) in clusters.iter().enumerate() {
    println!("Cluster {}: {} points", i, cluster.len());
}
```

### DBSCAN

```rust
use clustering_algorithms_suite::{DBSCAN, Point};

let points = vec![/* ... */];
let epsilon = 0.5;    // Neighborhood radius
let min_points = 3;   // Minimum points to form cluster

let dbscan = DBSCAN::new(epsilon, min_points);
let clusters = dbscan.fit(&points);
```

## 📊 Complexity Analysis

| Algorithm | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **K-Means** | $O(nki)$ | $O(n + k)$ |
| **K-Medoids** | $O(n^2ki)$ | $O(n^2)$ |
| **DBSCAN** | $O(n \log n)$ | $O(n)$ |

Where:
- $n$ = number of points
- $k$ = number of clusters
- $i$ = number of iterations

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
