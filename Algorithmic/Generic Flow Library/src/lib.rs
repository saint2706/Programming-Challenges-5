use std::collections::{HashMap, VecDeque};
use std::cmp::min;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct NodeId(pub usize);

#[derive(Clone, Debug)]
struct Edge {
    to: NodeId,
    capacity: i32,
    flow: i32,
    rev_edge: usize, // Index of reverse edge in adjacency list of `to`
}

/// Edmonds-Karp algorithm implementation for Max Flow.
pub struct MaxFlow {
    adj: HashMap<NodeId, Vec<Edge>>,
}

impl MaxFlow {
    pub fn new() -> Self {
        MaxFlow {
            adj: HashMap::new(),
        }
    }

    /// Adds a directed edge with capacity.
    /// Automatically adds a reverse edge with 0 capacity for residual graph.
    pub fn add_edge(&mut self, u: NodeId, v: NodeId, cap: i32) {
        let u_idx = self.adj.entry(u.clone()).or_default().len();
        let v_idx = self.adj.entry(v.clone()).or_default().len();

        self.adj.get_mut(&u).unwrap().push(Edge {
            to: v.clone(),
            capacity: cap,
            flow: 0,
            rev_edge: v_idx,
        });

        self.adj.get_mut(&v).unwrap().push(Edge {
            to: u,
            capacity: 0, // Reverse edge has 0 capacity in original graph
            flow: 0,
            rev_edge: u_idx,
        });
    }

    pub fn edmonds_karp(&mut self, source: NodeId, sink: NodeId) -> i32 {
        let mut max_flow = 0;

        loop {
            // BFS to find augmenting path in residual graph
            let mut parent = HashMap::new();
            // Store (node, edge_index) in parent map to easily update flow
            let mut queue = VecDeque::new();

            queue.push_back(source.clone());
            parent.insert(source.clone(), None); // Sentinel

            let mut path_found = false;
            while let Some(u) = queue.pop_front() {
                if u == sink {
                    path_found = true;
                    break;
                }

                if let Some(edges) = self.adj.get(&u) {
                    for (i, edge) in edges.iter().enumerate() {
                        if !parent.contains_key(&edge.to) && edge.capacity > edge.flow {
                            parent.insert(edge.to.clone(), Some((u.clone(), i)));
                            queue.push_back(edge.to.clone());
                        }
                    }
                }
            }

            if !path_found {
                break;
            }

            // Find bottleneck capacity
            let mut path_flow = i32::MAX;
            let mut curr = sink.clone();
            while curr != source {
                if let Some(Some((prev, edge_idx))) = parent.get(&curr) {
                    let edge = &self.adj[prev][*edge_idx];
                    path_flow = min(path_flow, edge.capacity - edge.flow);
                    curr = prev.clone();
                } else {
                    panic!("Broken path reconstruction");
                }
            }

            // Update residual capacities
            max_flow += path_flow;
            let mut curr = sink.clone();
            while curr != source {
                if let Some(Some((prev, edge_idx))) = parent.get(&curr) {
                    // Update forward edge
                    let edge = &mut self.adj.get_mut(prev).unwrap()[*edge_idx];
                    edge.flow += path_flow;
                    let rev_idx = edge.rev_edge;

                    // Update reverse edge
                    let rev_edge = &mut self.adj.get_mut(&curr).unwrap()[rev_idx];
                    rev_edge.flow -= path_flow;

                    curr = prev.clone();
                }
            }
        }

        max_flow
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_max_flow_simple() {
        let mut graph = MaxFlow::new();
        let s = NodeId(0);
        let t = NodeId(1);

        graph.add_edge(s.clone(), t.clone(), 10);

        assert_eq!(graph.edmonds_karp(s, t), 10);
    }

    #[test]
    fn test_max_flow_complex() {
        let mut graph = MaxFlow::new();
        let s = NodeId(0);
        let a = NodeId(1);
        let b = NodeId(2);
        let t = NodeId(3);

        graph.add_edge(s.clone(), a.clone(), 10);
        graph.add_edge(s.clone(), b.clone(), 10);
        graph.add_edge(a.clone(), b.clone(), 2);
        graph.add_edge(a.clone(), t.clone(), 4);
        graph.add_edge(b.clone(), t.clone(), 8);

        assert_eq!(graph.edmonds_karp(s, t), 12);
    }
}
