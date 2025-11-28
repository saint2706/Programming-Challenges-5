# Online Caching Simulator

A simulator for various cache replacement policies including LRU, LFU, FIFO, and optimal (Belady's algorithm).

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Caching** stores frequently accessed data in fast memory to improve performance. When the cache is full, a **replacement policy** decides which item to evict.

### Policies Implemented
1. **LRU (Least Recently Used)**: Evict the item accessed longest ago
2. **LFU (Least Frequently Used)**: Evict the item accessed least often
3. **FIFO (First In First Out)**: Evict the oldest item
4. **Optimal (Belady's)**: Evict the item that will be used furthest in the future (requires future knowledge)

### LRU Implementation
Uses a doubly-linked list + hash map:
- **Hash map**: O(1) lookup
- **Linked list**: O(1) move-to-front for access

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use online_caching_simulator::{LRUCache, CachePolicy};

// Create LRU cache with capacity 3
let mut cache = LRUCache::new(3);

cache.access(1);  // Cache: [1]
cache.access(2);  // Cache: [2, 1]
cache.access(3);  // Cache: [3, 2, 1]
cache.access(4);  // Cache: [4, 3, 2], evicts 1

// Check hit/miss statistics
println!("Hit rate: {:.2}%", cache.hit_rate() * 100.0);
```

## 📊 Complexity Analysis

| Policy | Access Time | Space |
| :--- | :--- | :--- |
| **LRU** | $O(1)$ | $O(k)$ |
| **LFU** | $O(\log k)$ | $O(k)$ |
| **FIFO** | $O(1)$ | $O(k)$ |

Where $k$ is the cache capacity.

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
