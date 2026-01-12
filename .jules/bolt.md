# Bolt's Journal

This journal tracks critical performance learnings.

## 2026-01-02 - Optimizing Reservoir Sampling Queries

**Learning:** For a reservoir sampling implementation used for quantile queries, the order of elements in the pool is irrelevant for the sampling logic (which picks a random index to replace). However, `query()` operations require a sorted pool. Sorting the pool in-place (`pool.sort()`) instead of creating a sorted copy (`sorted(pool)`) provides a massive speedup (6x) for interleaved query/insert workloads because Timsort is extremely efficient on the partially-sorted data that results from subsequent inserts.
**Action:** When maintaining a collection for order statistics where insertion order doesn't matter, keep the collection sorted (or sort in-place lazily) to optimize read performance.
