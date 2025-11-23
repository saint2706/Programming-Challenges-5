# Versioned Key-Value Store (LSM-tree)

## Theory
This challenge implements a persistent Key-Value Store using a **Log-Structured Merge-tree (LSM-tree)** architecture. This structure is optimized for write-heavy workloads (e.g., BigTable, Cassandra, RocksDB).

1.  **MemTable (Memory):** Writes first go to an in-memory structure (hash map or skip list). This allows fast $O(1)$ or $O(\log N)$ writes.
2.  **SSTable (Disk):** When the MemTable reaches a size limit, it is flushed to disk as a **Sorted String Table (SSTable)**. The file is immutable and sorted by key.
3.  **Read Path:** To read a key, check the MemTable first. If not found, check SSTables on disk, starting from the most recent.
4.  **Compaction:** Over time, many SSTables accumulate. Compaction merges them into a single, larger SSTable, discarding overwritten values and tombstones (deleted keys).

## Installation
No external dependencies.

## Usage
```bash
python main.py
```

## Complexity Analysis
*   **Write:** $O(1)$ (append to MemTable).
*   **Read:** $O(M + K \cdot \log N)$ where $M$ is MemTable lookup, $K$ is number of SSTables, and $N$ is entries per SSTable. With Bloom Filters (not implemented here) and binary search, this is fast.
*   **Space:** $O(N)$. Compaction reclaims space from updates/deletes.

## Demos
Run `main.py` to observe put/get operations, flushing to disk (check `lsm_data/` folder), and compaction.
