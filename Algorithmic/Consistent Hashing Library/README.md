# Consistent Hashing

A demonstration of Consistent Hashing, a technique used in distributed systems to distribute data across nodes in a way that minimizes reorganization when nodes are added or removed.

![Consistent Hashing Visualization](hash_ring_viz.gif)

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### The Ring

- Hash both **nodes** and **keys** onto the same circular space (e.g., $0$ to $2^{256}-1$).
- A key is assigned to the first node found moving clockwise from the key's position on the ring.

### Virtual Nodes (VNodes)

- To improve load balancing, each physical node is mapped to multiple points on the ring (virtual nodes).
- This prevents "hot spots" where one node handles a disproportionate amount of the keyspace.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

```python
from hash_ring import HashRing

# Create ring
hr = HashRing()

# Add nodes (with 100 virtual nodes each by default)
hr.add_node("Node A")
hr.add_node("Node B")
hr.add_node("Node C")

# Find which node handles a key
node = hr.lookup("my_user_id_123")[0]
print(f"Key mapped to: {node}")

# Distributed lookups (replication)
nodes = hr.lookup("critical_data", replicas=3)
print(f"Replicas: {nodes}")
```

## 📊 Complexity Analysis

| Operation       | Time Complexity                           |
| :-------------- | :---------------------------------------- |
| **Add Node**    | $O(V \cdot N \log (V \cdot N))$ (sorting) |
| **Remove Node** | $O(V \cdot N)$                            |
| **Lookup**      | $O(\log (V \cdot N))$ (Binary Search)     |

Where $N$ is the number of physical nodes and $V$ is the number of virtual nodes per physical node.

## 🎬 Demos

### Generating the Animation

To generate the Consistent Hashing visualization:

```bash
manim -pql visualize_hash_ring.py ConsistentHashingDemo
```
