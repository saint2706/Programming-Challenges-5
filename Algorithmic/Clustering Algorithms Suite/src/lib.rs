use rand::Rng;
use std::collections::HashSet;

#[derive(Clone, Debug, PartialEq)]
pub struct Point {
    pub coords: Vec<f64>,
}

impl Point {
    pub fn new(coords: Vec<f64>) -> Self {
        Point { coords }
    }

    pub fn distance(&self, other: &Point) -> f64 {
        self.coords
            .iter()
            .zip(other.coords.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>()
            .sqrt()
    }
}

/// K-Means clustering algorithm.
pub struct KMeans {
    k: usize,
    max_iters: usize,
}

impl KMeans {
    pub fn new(k: usize, max_iters: usize) -> Self {
        KMeans { k, max_iters }
    }

    pub fn fit(&self, points: &[Point]) -> Vec<usize> {
        if points.is_empty() {
            return vec![];
        }

        let mut rng = rand::rng();
        let mut centroids: Vec<Point> = (0..self.k)
            .map(|_| points[rng.random_range(0..points.len())].clone())
            .collect();

        let mut assignments = vec![0; points.len()];

        for _ in 0..self.max_iters {
            let mut changed = false;

            // Assign points to nearest centroid
            for (i, point) in points.iter().enumerate() {
                let mut min_dist = f64::MAX;
                let mut best_cluster = 0;
                for (j, centroid) in centroids.iter().enumerate() {
                    let dist = point.distance(centroid);
                    if dist < min_dist {
                        min_dist = dist;
                        best_cluster = j;
                    }
                }
                if assignments[i] != best_cluster {
                    assignments[i] = best_cluster;
                    changed = true;
                }
            }

            if !changed {
                break;
            }

            // Update centroids
            let mut new_centroids = vec![vec![0.0; points[0].coords.len()]; self.k];
            let mut counts = vec![0; self.k];

            for (i, point) in points.iter().enumerate() {
                let cluster = assignments[i];
                for (d, val) in point.coords.iter().enumerate() {
                    new_centroids[cluster][d] += val;
                }
                counts[cluster] += 1;
            }

            for j in 0..self.k {
                if counts[j] > 0 {
                    for d in 0..centroids[j].coords.len() {
                        centroids[j].coords[d] = new_centroids[j][d] / counts[j] as f64;
                    }
                } else {
                    // If a cluster is empty, re-initialize it to a random point
                     centroids[j] = points[rng.random_range(0..points.len())].clone();
                }
            }
        }

        assignments
    }
}

/// DBSCAN clustering algorithm.
pub struct DBSCAN {
    epsilon: f64,
    min_points: usize,
}

impl DBSCAN {
    pub fn new(epsilon: f64, min_points: usize) -> Self {
        DBSCAN {
            epsilon,
            min_points,
        }
    }

    pub fn fit(&self, points: &[Point]) -> Vec<i32> {
        let n = points.len();
        let mut labels = vec![-2; n]; // -2 undefined
        let mut current_c = -1;

        for i in 0..n {
            if labels[i] != -2 {
                continue;
            }
            let neighbors = self.region_query(points, i);
            if neighbors.len() < self.min_points {
                labels[i] = -1; // Noise
            } else {
                current_c += 1;
                self.expand(points, &mut labels, i, neighbors, current_c);
            }
        }

        labels
    }

    fn expand(&self, points: &[Point], labels: &mut Vec<i32>, root: usize, mut neighbors: Vec<usize>, c: i32) {
        labels[root] = c;

        let mut i = 0;
        while i < neighbors.len() {
            let neighbor_idx = neighbors[i];
            if labels[neighbor_idx] == -1 {
                labels[neighbor_idx] = c; // Change noise to border point
            } else if labels[neighbor_idx] == -2 {
                labels[neighbor_idx] = c;
                let new_neighbors = self.region_query(points, neighbor_idx);
                if new_neighbors.len() >= self.min_points {
                    neighbors.extend(new_neighbors);
                }
            }
            i += 1;
        }
    }

    fn region_query(&self, points: &[Point], idx: usize) -> Vec<usize> {
        points.iter()
            .enumerate()
            .filter(|(_, p)| points[idx].distance(p) <= self.epsilon)
            .map(|(i, _)| i)
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kmeans_simple() {
        let points = vec![
            Point::new(vec![0.0, 0.0]),
            Point::new(vec![0.1, 0.1]),
            Point::new(vec![10.0, 10.0]),
            Point::new(vec![10.1, 10.1]),
        ];

        let kmeans = KMeans::new(2, 100);
        let assignments = kmeans.fit(&points);

        assert_eq!(assignments.len(), 4);
        // Should be 2 clusters. Points 0,1 should be same, 2,3 same.
        assert_eq!(assignments[0], assignments[1]);
        assert_eq!(assignments[2], assignments[3]);
        assert_ne!(assignments[0], assignments[2]);
    }

    #[test]
    fn test_dbscan_simple() {
        // Cluster 1: (0,0), (0,1), (1,0), (1,1) -> dense square
        // Noise: (5,5)
        // Cluster 2: (10,10), (10,11), (11,10), (11,11)

        let points = vec![
            Point::new(vec![0.0, 0.0]), Point::new(vec![0.0, 1.0]),
            Point::new(vec![1.0, 0.0]), Point::new(vec![1.0, 1.0]),
            Point::new(vec![5.0, 5.0]), // Noise
            Point::new(vec![10.0, 10.0]), Point::new(vec![10.0, 11.0]),
            Point::new(vec![11.0, 10.0]), Point::new(vec![11.0, 11.0]),
        ];

        // Eps=1.5, MinPts=3
        // (0,0) neighbors: (0,1), (1,0), (1,1) (dist sqrt(2) ~ 1.414) -> count 4 >= 3. Core.
        // (5,5) neighbors: self -> count 1. Noise.

        let dbscan = DBSCAN::new(1.5, 3);
        let labels = dbscan.fit(&points);

        assert_eq!(labels[0], labels[1]);
        assert_eq!(labels[0], labels[2]);
        assert_eq!(labels[0], labels[3]);

        assert_eq!(labels[4], -1); // Noise

        assert_eq!(labels[5], labels[6]);
        assert_eq!(labels[5], labels[7]);
        assert_eq!(labels[5], labels[8]);

        assert_ne!(labels[0], labels[5]);
    }
}
