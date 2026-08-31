# Optimal Solution: K-d Tree & Nearest Neighbors

**Challenge:** organise points in `k`-dimensional space so nearest-neighbour
queries are fast.

**Short answer:** there is no single optimal structure — there is one per
_dimensionality_, and the crossovers are sharp. A k-d tree is optimal in **two
to four dimensions**. Above that, a vectorised brute-force scan is both simpler
and faster for exact search; above about fifteen, approximate search via
**HNSW** is the only thing that is sublinear at all. Implementation:
[`optimal_nn.py`](optimal_nn.py).

The measured crossover is at **d ≈ 4–5**, not the `d > 20` figure this
directory's README currently quotes. That correction is the main finding here,
and section 3 explains why both numbers are right about different things.

---

## 1. The optimal k-d tree: no nodes, no pointers

A textbook k-d tree allocates an object per point with two child references. In
CPython that is ~100 bytes of overhead per point and a pointer chase per level.
Both are avoidable.

**Store the tree implicitly.** Permute the points once so the structure is
_implied by index arithmetic_: the subtree covering array range `[lo, hi)` has
its root at `(lo + hi) // 2`, children in `[lo, m)` and `[m+1, hi)`. Exactly like
a binary heap, there is nothing to store but the points and one split axis per
node. Points near each other in the tree are then near each other in memory, so
a traversal walks contiguous cache lines instead of chasing pointers. (Wald 2022
develops this layout, plus a stack-free traversal, for GPUs; the same idea pays
on a CPU.)

**Split on the widest-spread axis, not a cycled one.** Cycling `x, y, z, x, …`
is simpler and noticeably worse on anisotropic data: points spread over a long
thin region get split repeatedly along the _short_ axis, producing slivers that
prune badly. One byte per node buys the better rule. `test_split_axis_follows_
the_widest_spread` pins it.

**Build in `O(n log n)` with `argpartition`.** Median selection is `O(n)` per
level via introselect — no sorting needed. NumPy's `argpartition` is that
algorithm, so each level costs one C call.

**Prune at pop time, not push time.** When descending, the far side of a split
is only worth visiting if the splitting plane is closer than the current worst
neighbour. Checking that when the branch is _pushed_ uses a bound that is
usually stale; re-checking when it is _popped_ — after the near side has
improved the neighbour set — prunes far more. Same code, tighter bound.

### The Python-specific decision, which goes against the usual advice

The build uses NumPy. **The query deliberately does not.** Per-point NumPy
scalar arithmetic carries more interpreter overhead than a plain Python loop
over a handful of coordinates, so the traversal keeps points as a list of
tuples. This is worth about 3×.

"Vectorise everything" is the right default and the wrong answer here, because
the traversal visits points _one at a time by nature_ — there is no batch to
vectorise over. That observation is also what motivates the next section: if the
access pattern cannot be vectorised, maybe the algorithm that needs it is the
wrong algorithm.

## 2. Measured: where each structure wins

20 000 points, 30 queries, `k = 10`, CPython 3.11 with NumPy on OpenBLAS:

| dim |    k-d tree | Brute force (NumPy) | Winner           |
| --: | ----------: | ------------------: | :--------------- |
|   2 | **0.06 ms** |             2.17 ms | k-d tree, 35×    |
|   4 | **0.31 ms** |             0.41 ms | k-d tree, 1.3×   |
|   8 |     8.16 ms |         **0.30 ms** | brute force, 27× |
|  16 |    38.11 ms |         **1.35 ms** | brute force, 28× |
|  32 |    61.89 ms |         **0.72 ms** | brute force, 86× |

Both columns are exact and verified to return identical results.

Approximate search, 5 000 points in 64 dimensions, `k = 10`:

| Method         | Time/query | Recall |
| :------------- | ---------: | -----: |
| HNSW, `ef=20`  |    0.84 ms |  0.766 |
| HNSW, `ef=50`  |    1.58 ms |  0.884 |
| HNSW, `ef=150` |    3.93 ms |  0.966 |
| Exact k-d tree |   27.13 ms |  1.000 |

## 3. Why the crossover is at d ≈ 4, not d ≈ 20

Both numbers are correct; they measure different things.

**`d ≈ 20` is where the k-d tree stops pruning.** As dimension rises, the volume
of a ball shrinks relative to the bounding box that encloses it, so the
splitting plane is almost always closer than the current best neighbour and
almost no branch can be discarded. By `d ≈ 20` the tree examines essentially
every point. That is a statement about the _algorithm_, and it is
implementation-independent.

**`d ≈ 4` is where the tree stops being worth its constant factor.** Long before
pruning fails outright, it merely degrades — and it only has to degrade a little
before an interpreted traversal loses to BLAS. Brute force is a single
`queries @ points.T`: multi-threaded, blocked, SIMD, running at several GFLOP/s.
The tree walks nodes in Python bytecode. The tree can be visiting 50× fewer
points and still lose, because it is paying perhaps 500× more per point.

So the practical rule in Python is **`d ≤ 4`: build a tree. `d ≥ 5`: multiply
matrices.** In C or Rust the crossover moves back up toward the textbook figure,
because the per-point costs become comparable. `KD_TREE_DIMENSION_LIMIT` in the
module encodes the measured value rather than the folklore one.

The wider lesson: asymptotic analysis says which algorithm examines fewer
elements; it does not say which program finishes first. Both matter, and the
constant-factor gap between interpreted and vectorised code is large enough to
overturn an asymptotic advantage across a useful range of inputs.

## 4. High dimension: HNSW

Once exactness can be traded away, **Hierarchical Navigable Small World** graphs
(Malkov & Yashunin 2016/2018) are the state of the art, and what essentially
every production vector database is built on.

Build a proximity graph and answer a query by greedy walk: step to whichever
neighbour is closer to the query. A plain proximity graph gets stuck in local
minima and takes many hops to cross the space. HNSW fixes both:

- **Hierarchy.** Each point gets a maximum level from an exponentially decaying
  distribution, so upper layers hold exponentially fewer points and carry
  long-range edges. Search descends the layers, each one supplying a better
  starting point for the next — a skip list's trick, transplanted into a metric
  space.
- **Beam search, not greedy.** Layer 0 is searched with a candidate set of size
  `ef` rather than a single best, which is what escapes local minima.

`ef` is the accuracy dial, and the crucial property is that it is a **query-time
parameter**: recall can be traded for latency per call, without rebuilding. The
table above shows it spanning 0.77 → 0.97 recall over a 4.7× latency range on
one index.

Two implementation notes. The level scale `1/ln(M)` makes the expected layer
count `log_M(n)`, balancing descent cost against layer count. And when a node
exceeds its degree budget, the over-degree neighbours must be pruned by
_distance_ rather than arbitrarily — dropping the wrong edges destroys
navigability, which shows up as a recall ceiling that no `ef` can lift.

**Honest limitation:** the build in this implementation takes 17 s for 5 000
points, because each insertion runs its own beam search in interpreted Python.
It is a reference implementation of the algorithm, not a production index; for
that, use `hnswlib` or FAISS, which implement the same algorithm in C++ with
SIMD distance kernels. The algorithm is the deliverable here, and the query path
— which batches each expansion's distances through NumPy — is representative.

## 5. Non-optimal alternatives, and why each loses

| Alternative                                       | Verdict                                                                                                                                                                                                                                                                                                                      |
| :------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pointer-based k-d tree with cycled axes**       | The textbook version and the current `kd_tree.py`. Correct; pays ~100 bytes/point of object overhead, a pointer chase per level, and splits badly on anisotropic data.                                                                                                                                                       |
| **Sorting to find each median**                   | `O(n log² n)` build instead of `O(n log n)`. `argpartition` is strictly better and no harder to use.                                                                                                                                                                                                                         |
| **Ball tree**                                     | Splits by enclosing hyperspheres rather than axis-aligned boxes, so it prunes better in moderate dimension and works in any metric. Slower to build, and in Python it loses to brute force at the same low crossover. Choose it over a k-d tree when the metric is not Euclidean.                                            |
| **VP-tree / metric tree**                         | Also metric-general, using distance-to-pivot rather than coordinates. Same conclusion as ball trees; the right pick when coordinates do not exist (edit distance, graph distance).                                                                                                                                           |
| **R-tree**                                        | Built for _extended objects_ (rectangles, polygons) and range queries, not points and k-NN. Using it here imports bulk-loading and node-splitting machinery for no benefit.                                                                                                                                                  |
| **Grid / uniform bucketing**                      | Excellent for uniformly distributed low-dimensional points, and it beats a k-d tree when the data really is uniform. Degenerates badly on clustered data — the case that motivates a tree in the first place. Cell count is `O(1/h^d)`, so it dies immediately as `d` grows.                                                 |
| **Locality-sensitive hashing**                    | The classic sublinear approximate method, with provable guarantees. Superseded in practice by HNSW, which achieves better recall at lower latency across essentially every published benchmark. LSH keeps an edge where its theoretical guarantees are required, or where the index must be distributed and updated cheaply. |
| **IVF-PQ / ScaNN**                                | Quantisation-based approximate search. Beats HNSW on _memory_ by an order of magnitude, at some recall cost — the reason billion-scale systems use it. For in-memory indexes at the scale here, HNSW is faster at equal recall.                                                                                              |
| **Cover tree**                                    | Elegant `O(log n)` guarantees under bounded intrinsic dimension. Constants are poor enough that it rarely wins in practice; a theory result.                                                                                                                                                                                 |
| **`scipy.spatial.cKDTree` / `sklearn.neighbors`** | What you should actually use in production: the same algorithms with C implementations, and their crossover sits at the textbook `d ≈ 20` rather than at 4. This module exists to show the algorithms, not to compete with them.                                                                                             |

### Deliberately not implemented

**Stack-free traversal** (Wald 2022). The implicit layout permits recovering the
parent by index arithmetic, so a query needs no traversal stack at all — which
matters enormously on a GPU, where per-thread stack space is scarce. On a CPU
running Python, the stack is a list and costs nothing worth removing. The layout
that makes it possible is implemented; the traversal trick is not.

**Sliding-midpoint splitting** (Maneewongvatana & Mount). Splits at the midpoint
of the bounding box rather than the median, sliding to avoid empty cells.
Produces better-shaped cells for clustered data at the cost of an unbalanced
tree — which the implicit array layout cannot represent, since that layout
_requires_ a balanced split. A genuine trade-off, resolved here in favour of the
pointer-free representation.

## 6. Choosing

```
Exact results required?
├── Yes
│   ├── d <= 4  and n >= 1000 ──► ImplicitKdTree     (35x at d=2)
│   └── otherwise ─────────────► brute_force_knn     (BLAS; 86x at d=32)
└── No (approximate acceptable)
    ├── d > 5, n >= 10,000 ────► HNSW                (~0.97 recall at ef=150)
    └── memory-constrained ────► IVF-PQ / ScaNN      (not implemented)
```

`recommend_structure(n, dim, exact)` returns exactly this.

## 7. Complexity summary

| Operation                  | Time                                                | Space                           |
| :------------------------- | :-------------------------------------------------- | :------------------------------ |
| `ImplicitKdTree` build     | `O(n log n)`                                        | `O(n)`, no per-node objects     |
| `ImplicitKdTree.k_nearest` | `O(log n)` expected at low `d`; `O(n)` as `d` grows | `O(log n)` stack                |
| `brute_force_knn`          | `O(nmd)` at BLAS speed                              | `O(nm)` for the distance matrix |
| `HNSW` build               | `O(n log n · ef)` distance computations             | `O(n · M)` edges                |
| `HNSW.query`               | `O(log n · ef)` expected                            | `O(ef)`                         |

---

## References

- Bentley, _Multidimensional binary search trees used for associative searching_, CACM 18(9), 1975.
- Friedman, Bentley, Finkel, _An algorithm for finding best matches in logarithmic expected time_, ACM TOMS 3(3), 1977.
- Maneewongvatana & Mount, _Analysis of approximate nearest neighbor searching with clustered point sets_, ALENEX 1999. (Sliding midpoint.)
- Wald, [_GPU-friendly, Parallel, and (Almost-)In-Place Construction of Left-Balanced k-d Trees_](https://arxiv.org/abs/2211.00120), 2022, and [_A Stack-Free Traversal Algorithm for Left-Balanced k-d Trees_](https://arxiv.org/abs/2210.12859), 2022.
- Malkov & Yashunin, _Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs_, IEEE TPAMI 42(4), 2020 (arXiv 2016).
- Beyer, Goldstein, Ramakrishnan, Shaft, _When is "nearest neighbor" meaningful?_, ICDT 1999. (The curse of dimensionality, stated precisely.)
- Guo et al., _Accelerating large-scale inference with anisotropic vector quantization_, ICML 2020. (ScaNN.)
