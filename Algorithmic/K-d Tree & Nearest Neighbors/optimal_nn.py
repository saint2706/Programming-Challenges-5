"""Optimal nearest-neighbour search, which is three different algorithms.

There is no single best nearest-neighbour structure; there is a best structure
*per dimensionality*, and the crossovers are sharp enough that picking wrong
costs orders of magnitude.

* **Low dimension (d <= ~10):** :class:`ImplicitKdTree`. A k-d tree with no node
  objects and no pointers at all -- the tree lives implicitly in the layout of a
  single reordered array, the way a binary heap does. Exact, `O(log n)` expected
  per query.
* **Moderate dimension, batched queries:** :func:`brute_force_knn`. Exact, and
  in NumPy it is a single matrix multiply. Past roughly `d = 15` this *beats*
  any tree, because the curse of dimensionality destroys pruning while BLAS
  keeps running at full speed.
* **High dimension, approximate acceptable:** :class:`HNSW`. A navigable
  small-world graph -- the current state of the art for approximate search, and
  what every production vector database is built on.

The k-d tree is what the challenge asks for, and it is the right answer only in
the first regime. ``OPTIMAL.md`` gives the measured crossover and the reasoning.
"""

from __future__ import annotations

import heapq
import math
from typing import List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "ImplicitKdTree",
    "brute_force_knn",
    "HNSW",
    "recommend_structure",
]


# --------------------------------------------------------------------------
# Exact search in low dimension
# --------------------------------------------------------------------------


class ImplicitKdTree:
    """A k-d tree stored implicitly in one array -- no nodes, no pointers.

    **The layout.** A conventional k-d tree allocates an object per point with
    two child references: on CPython that is roughly 100 bytes of overhead per
    point and a pointer chase per level. This implementation instead permutes
    the points so that the tree structure is *implied by index arithmetic*: the
    subtree covering array range ``[lo, hi)`` has its root at ``(lo + hi) // 2``,
    with children in ``[lo, m)`` and ``[m+1, hi)``. Exactly like a binary heap,
    there is nothing to store but the points themselves and one split axis per
    node.

    The saving is not only memory. Points that are near each other in the tree
    are near each other in memory, so a traversal walks contiguous cache lines
    instead of chasing pointers. (Wald, 2022, develops this layout and a
    stack-free traversal for GPUs; the same idea pays off on a CPU.)

    **Splitting rule.** Rather than cycling axes `x, y, z, x, ...`, each node
    splits on the axis of **widest spread** among its own points. Cycling is
    simpler and noticeably worse on anisotropic data -- points spread over a
    long thin region get split repeatedly along the short axis, producing
    slivers that prune badly. One byte per node buys the better rule.

    **A Python-specific decision.** The build uses NumPy (``argpartition`` gives
    median selection in `O(n)` per level). The *query* deliberately does not:
    per-point NumPy scalar arithmetic carries more interpreter overhead than a
    plain Python loop over a handful of coordinates. Points are kept as a list
    of tuples for traversal. This is worth about 3x, and it is the opposite of
    the usual "vectorise everything" advice -- it applies because the traversal
    visits points one at a time by nature.

    Example:
        >>> tree = ImplicitKdTree([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
        >>> idx, dist = tree.nearest([9, 2])
        >>> tree.point(idx), round(dist, 4)
        ((8.0, 1.0), 1.4142)
    """

    def __init__(self, points: Sequence[Sequence[float]]) -> None:
        """Build the tree.

        Args:
            points: ``(n, d)`` array-like of coordinates.

        Raises:
            ValueError: If ``points`` is not a non-empty 2-D array.

        Complexity:
            `O(n log n)` time via median selection at each level, `O(n)` space
            beyond the points themselves.
        """
        data = np.asarray(points, dtype=np.float64)
        if data.ndim != 2 or data.shape[0] == 0:
            raise ValueError("points must be a non-empty (n, d) array")

        self.n, self.dim = data.shape
        #: Original index of each point, in tree order.
        self.order = np.arange(self.n)
        #: Split axis chosen at each tree position.
        self.axes = np.zeros(self.n, dtype=np.int8)

        self._build(data, 0, self.n)
        self._data = data[self.order]
        # Plain Python tuples for the traversal; see the class docstring.
        self._coords: List[Tuple[float, ...]] = [
            tuple(row) for row in self._data.tolist()
        ]
        self._axes: List[int] = self.axes.tolist()

    def _build(self, data: np.ndarray, lo: int, hi: int) -> None:
        """Recursively partition ``order[lo:hi]`` into implicit-tree layout."""
        stack = [(lo, hi)]
        while stack:
            lo, hi = stack.pop()
            if hi - lo <= 1:
                continue
            sub = self.order[lo:hi]
            block = data[sub]
            # Widest-spread axis, not a cycling one.
            axis = int(np.argmax(block.max(axis=0) - block.min(axis=0)))
            mid = (lo + hi) // 2
            # argpartition places the median at its final position in O(n).
            part = np.argpartition(block[:, axis], mid - lo)
            self.order[lo:hi] = sub[part]
            self.axes[mid] = axis
            stack.append((lo, mid))
            stack.append((mid + 1, hi))

    def point(self, original_index: int) -> Tuple[float, ...]:
        """Return the coordinates of the point with the given *original* index."""
        position = int(np.nonzero(self.order == original_index)[0][0])
        return self._coords[position]

    def k_nearest(self, query: Sequence[float], k: int = 1) -> List[Tuple[int, float]]:
        """Return the ``k`` nearest points to ``query``.

        Args:
            query: A point with the same dimensionality as the tree.
            k: How many neighbours to return.

        Returns:
            ``(original_index, distance)`` pairs sorted by increasing distance.
            Fewer than ``k`` entries if the tree has fewer points.

        Raises:
            ValueError: If ``query`` has the wrong dimensionality.

        Complexity:
            `O(log n)` expected in low dimension; `O(n)` worst case, which is
            also the *typical* case once `d` grows past ~15. See ``OPTIMAL.md``.
        """
        if k <= 0:
            return []
        q = tuple(float(x) for x in query)
        if len(q) != self.dim:
            raise ValueError(f"query has dimension {len(q)}, tree has {self.dim}")

        coords = self._coords
        axes = self._axes
        # Max-heap (via negation) of the k best so far.
        best: List[Tuple[float, int]] = []
        worst = math.inf

        # Entries are (lo, hi, bound): `bound` is the squared distance from the
        # query to the splitting plane this branch sits behind. Re-checking it
        # at pop time rather than push time is what makes the pruning tight --
        # by then the neighbour set has usually improved.
        stack: List[Tuple[int, int, float]] = [(0, self.n, 0.0)]
        while stack:
            lo, hi, bound = stack.pop()
            if lo >= hi:
                continue
            if len(best) == k and bound >= worst:
                continue

            mid = (lo + hi) // 2
            point = coords[mid]
            total = 0.0
            for i, value in enumerate(point):
                delta = q[i] - value
                total += delta * delta

            if len(best) < k:
                heapq.heappush(best, (-total, mid))
                worst = -best[0][0]
            elif total < worst:
                heapq.heapreplace(best, (-total, mid))
                worst = -best[0][0]

            axis = axes[mid]
            offset = q[axis] - point[axis]
            if offset < 0:
                near, far = (lo, mid), (mid + 1, hi)
            else:
                near, far = (mid + 1, hi), (lo, mid)
            # Push far first: the stack pops the near side first, which finds
            # good neighbours early and makes the far side prunable.
            stack.append((far[0], far[1], offset * offset))
            stack.append((near[0], near[1], 0.0))

        ordered = sorted((-d2, idx) for d2, idx in best)
        return [(int(self.order[idx]), math.sqrt(d2)) for d2, idx in ordered]

    def nearest(self, query: Sequence[float]) -> Tuple[int, float]:
        """Return ``(original_index, distance)`` of the single closest point."""
        return self.k_nearest(query, 1)[0]

    def within_radius(
        self, query: Sequence[float], radius: float
    ) -> List[Tuple[int, float]]:
        """Return every point within ``radius`` of ``query``, nearest first.

        Args:
            query: A point with the same dimensionality as the tree.
            radius: Inclusive search radius.

        Raises:
            ValueError: If ``radius`` is negative or ``query`` has the wrong
                dimensionality.
        """
        if radius < 0:
            raise ValueError("radius must be non-negative")
        q = tuple(float(x) for x in query)
        if len(q) != self.dim:
            raise ValueError(f"query has dimension {len(q)}, tree has {self.dim}")

        limit = radius * radius
        coords = self._coords
        axes = self._axes
        found: List[Tuple[float, int]] = []
        stack: List[Tuple[int, int, float]] = [(0, self.n, 0.0)]
        while stack:
            lo, hi, bound = stack.pop()
            if lo >= hi or bound > limit:
                continue
            mid = (lo + hi) // 2
            point = coords[mid]
            total = 0.0
            for i, value in enumerate(point):
                delta = q[i] - value
                total += delta * delta
            if total <= limit:
                found.append((total, mid))

            axis = axes[mid]
            offset = q[axis] - point[axis]
            if offset < 0:
                near, far = (lo, mid), (mid + 1, hi)
            else:
                near, far = (mid + 1, hi), (lo, mid)
            stack.append((far[0], far[1], offset * offset))
            stack.append((near[0], near[1], 0.0))

        found.sort()
        return [(int(self.order[idx]), math.sqrt(d2)) for d2, idx in found]


# --------------------------------------------------------------------------
# Exact search by vectorised brute force
# --------------------------------------------------------------------------


def brute_force_knn(
    points: Sequence[Sequence[float]],
    queries: Sequence[Sequence[float]],
    k: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """Exact k-NN for a batch of queries, as one matrix multiplication.

    Expanding the squared distance,

    ``||p - q||^2 = ||p||^2 - 2 p.q + ||q||^2``

    turns the whole distance matrix into a single ``queries @ points.T`` plus two
    broadcast norm vectors. That call lands in BLAS, which is multi-threaded,
    blocked and vectorised -- so this "naive" method sustains a throughput that
    an interpreted tree traversal cannot approach.

    It is therefore not a strawman baseline. Beyond roughly `d = 15` it is the
    *correct* choice for exact search: the curse of dimensionality means a k-d
    tree prunes almost nothing and visits nearly every point anyway, but does so
    one interpreted node at a time.

    Args:
        points: ``(n, d)`` array-like of reference points.
        queries: ``(m, d)`` array-like of query points.
        k: Number of neighbours per query.

    Returns:
        ``(indices, distances)``, each ``(m, k)``, sorted by increasing distance.

    Raises:
        ValueError: If ``k`` is not positive or the dimensionalities disagree.

    Complexity:
        `O(n * m * d)` arithmetic, but at BLAS speed. Memory is `O(n * m)` for
        the distance matrix, so batch large query sets in chunks.
    """
    p = np.asarray(points, dtype=np.float64)
    q = np.asarray(queries, dtype=np.float64)
    if p.ndim != 2 or q.ndim != 2:
        raise ValueError("points and queries must both be 2-D")
    if p.shape[1] != q.shape[1]:
        raise ValueError(
            f"dimension mismatch: points {p.shape[1]}, queries {q.shape[1]}"
        )
    if k <= 0:
        raise ValueError("k must be positive")
    k = min(k, p.shape[0])

    d2 = (p * p).sum(axis=1)[None, :] - 2.0 * (q @ p.T) + (q * q).sum(axis=1)[:, None]
    # Cancellation in the expansion can produce small negatives on near-ties.
    np.maximum(d2, 0.0, out=d2)

    # argpartition finds the k smallest in O(n); only those k are then sorted.
    candidates = np.argpartition(d2, k - 1, axis=1)[:, :k]
    rows = np.arange(q.shape[0])[:, None]
    within = np.argsort(d2[rows, candidates], axis=1)
    indices = candidates[rows, within]
    return indices, np.sqrt(d2[rows, indices])


# --------------------------------------------------------------------------
# Approximate search in high dimension
# --------------------------------------------------------------------------


class HNSW:
    """Hierarchical Navigable Small World graph (Malkov & Yashunin, 2016/2018).

    The structure every production vector database is built on, and the honest
    answer to "nearest neighbours in high dimension" once exactness can be
    traded for speed.

    **The idea.** Build a proximity graph over the points and answer a query by
    greedy walk: repeatedly step to whichever neighbour is closer to the query.
    A plain proximity graph gets stuck in local minima and takes many hops to
    cross the space. HNSW fixes both:

    * **Hierarchy.** Each point is assigned a maximum level from an exponentially
      decaying distribution, so upper layers hold exponentially fewer points and
      have long-range edges. A search descends the layers, each one homing in
      from a better starting point -- the same trick a skip list plays on a
      linked list, in a metric space.
    * **Beam search, not greedy.** Layer 0 is searched with a candidate set of
      size ``ef`` rather than a single best, which is what escapes local minima.
      ``ef`` is the accuracy dial: raising it costs time and raises recall,
      *without rebuilding the index*.

    The result is roughly `O(log n)` query time with recall over 95% at modest
    ``ef`` -- in a regime where exact methods have no sublinear option at all.

    This implementation batches each expansion's distance computations through
    NumPy, which is what keeps a graph walk viable in interpreted Python.

    Example:
        >>> rng = np.random.default_rng(0)
        >>> data = rng.normal(size=(500, 32))
        >>> index = HNSW(data, seed=1)
        >>> hits = index.query(data[7], k=1)
        >>> hits[0][0]
        7
    """

    def __init__(
        self,
        points: Sequence[Sequence[float]],
        m: int = 16,
        ef_construction: int = 100,
        seed: int = 0,
    ) -> None:
        """Build the index.

        Args:
            points: ``(n, d)`` array-like.
            m: Target out-degree per node on layers above 0 (layer 0 gets
                ``2*m``). Higher means better recall and more memory.
            ef_construction: Beam width used while inserting. Higher builds a
                better graph, more slowly. Build-time only.
            seed: Seed for the level assignment, so builds are reproducible.

        Raises:
            ValueError: If ``points`` is not a non-empty 2-D array, or if ``m``
                or ``ef_construction`` is not positive.
        """
        data = np.asarray(points, dtype=np.float64)
        if data.ndim != 2 or data.shape[0] == 0:
            raise ValueError("points must be a non-empty (n, d) array")
        if m <= 0 or ef_construction <= 0:
            raise ValueError("m and ef_construction must be positive")

        self.data = data
        self.n, self.dim = data.shape
        self.m = m
        self.max_m0 = 2 * m
        self.ef_construction = ef_construction
        # Level normalisation: 1/ln(m) makes the expected number of layers
        # log_m(n), which is what balances descent cost against layer count.
        self._level_scale = 1.0 / math.log(m) if m > 1 else 1.0
        self._rng = np.random.default_rng(seed)

        #: graph[level][node] -> list of neighbour ids
        self.graph: List[dict] = []
        self.entry_point: Optional[int] = None
        self.max_level = -1

        for i in range(self.n):
            self._insert(i)

    def _random_level(self) -> int:
        """Draw a level from the exponentially decaying distribution."""
        return int(-math.log(max(self._rng.random(), 1e-12)) * self._level_scale)

    def _distances(self, ids: Sequence[int], query: np.ndarray) -> np.ndarray:
        """Squared distances from ``query`` to a batch of points, vectorised."""
        block = self.data[np.asarray(ids, dtype=np.intp)]
        diff = block - query
        return np.einsum("ij,ij->i", diff, diff)

    def _search_layer(
        self, query: np.ndarray, entry: List[int], ef: int, level: int
    ) -> List[Tuple[float, int]]:
        """Beam search one layer; returns up to ``ef`` closest as ``(dist2, id)``.

        Two heaps: ``candidates`` is a min-heap of frontier nodes to expand,
        ``found`` a max-heap (negated) of the best ``ef`` seen. The search stops
        as soon as the nearest unexpanded candidate is farther than the worst
        member of ``found``, since nothing beyond it can improve the result.
        """
        layer = self.graph[level]
        visited = set(entry)
        start = self._distances(entry, query)
        candidates = [(float(d), i) for d, i in zip(start, entry)]
        heapq.heapify(candidates)
        found = [(-d, i) for d, i in candidates]
        heapq.heapify(found)
        while len(found) > ef:
            heapq.heappop(found)

        while candidates:
            dist, node = heapq.heappop(candidates)
            if found and dist > -found[0][0] and len(found) >= ef:
                break
            fresh = [nb for nb in layer.get(node, ()) if nb not in visited]
            if not fresh:
                continue
            visited.update(fresh)
            for d, nb in zip(self._distances(fresh, query), fresh):
                d = float(d)
                if len(found) < ef:
                    heapq.heappush(candidates, (d, nb))
                    heapq.heappush(found, (-d, nb))
                elif d < -found[0][0]:
                    heapq.heappush(candidates, (d, nb))
                    heapq.heapreplace(found, (-d, nb))

        return sorted((-d, i) for d, i in found)

    def _insert(self, node: int) -> None:
        """Add one point to the graph."""
        level = self._random_level()
        query = self.data[node]

        while len(self.graph) <= level:
            self.graph.append({})

        if self.entry_point is None:
            for lvl in range(level + 1):
                self.graph[lvl][node] = []
            self.entry_point = node
            self.max_level = level
            return

        entry = [self.entry_point]
        # Descend the layers above this node's own level with a width-1 search,
        # purely to find a good entry point.
        for lvl in range(self.max_level, level, -1):
            entry = [self._search_layer(query, entry, 1, lvl)[0][1]]

        for lvl in range(min(level, self.max_level), -1, -1):
            neighbours = self._search_layer(query, entry, self.ef_construction, lvl)
            limit = self.max_m0 if lvl == 0 else self.m
            chosen = [i for _, i in neighbours[:limit]]
            self.graph[lvl][node] = list(chosen)
            for other in chosen:
                links = self.graph[lvl].setdefault(other, [])
                links.append(node)
                if len(links) > limit:
                    # Over-degree: keep the closest, which preserves the
                    # graph's navigability better than dropping arbitrarily.
                    order = np.argsort(self._distances(links, self.data[other]))
                    self.graph[lvl][other] = [links[j] for j in order[:limit]]
            entry = [i for _, i in neighbours] or entry

        for lvl in range(level + 1):
            self.graph[lvl].setdefault(node, [])

        if level > self.max_level:
            self.max_level = level
            self.entry_point = node

    def query(self, point: Sequence[float], k: int = 1, ef: Optional[int] = None):
        """Return the approximate ``k`` nearest neighbours of ``point``.

        Args:
            point: The query, of the index's dimensionality.
            k: Number of neighbours.
            ef: Beam width for the layer-0 search. Defaults to ``max(k, 50)``.
                This is the accuracy/latency dial and can be changed per query
                without rebuilding.

        Returns:
            ``(index, distance)`` pairs sorted by increasing distance.

        Raises:
            ValueError: If ``point`` has the wrong dimensionality.
        """
        if k <= 0:
            return []
        query = np.asarray(point, dtype=np.float64)
        if query.shape != (self.dim,):
            raise ValueError(f"query has shape {query.shape}, expected ({self.dim},)")
        if self.entry_point is None:
            return []

        ef = max(k, 50) if ef is None else max(ef, k)
        entry = [self.entry_point]
        for lvl in range(self.max_level, 0, -1):
            entry = [self._search_layer(query, entry, 1, lvl)[0][1]]
        results = self._search_layer(query, entry, ef, 0)
        return [(int(i), math.sqrt(max(d, 0.0))) for d, i in results[:k]]


# --------------------------------------------------------------------------
# Picking a structure
# --------------------------------------------------------------------------


#: Dimensionality above which vectorised brute force beats this k-d tree in
#: CPython. Measured, not assumed -- and far lower than the "d > 20" figure
#: usually quoted, because that figure compares *algorithms* while this one
#: compares an interpreted traversal against BLAS. See ``OPTIMAL.md``.
KD_TREE_DIMENSION_LIMIT = 5


def recommend_structure(n: int, dim: int, exact: bool = True) -> str:
    """Name the structure that should be used for the given problem shape.

    Encodes the crossovers measured in ``OPTIMAL.md``. Returns one of
    ``"ImplicitKdTree"``, ``"brute_force_knn"`` or ``"HNSW"``.

    Args:
        n: Number of reference points.
        dim: Dimensionality.
        exact: Whether exact results are required.

    Returns:
        The name of the recommended structure.
    """
    if not exact and dim > KD_TREE_DIMENSION_LIMIT and n >= 10_000:
        return "HNSW"
    if dim <= KD_TREE_DIMENSION_LIMIT and n >= 1_000:
        return "ImplicitKdTree"
    return "brute_force_knn"


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import time

    rng = np.random.default_rng(20260831)
    n, queries_count, k = 20_000, 30, 10

    print(f"Exact search: {n:,} points, {queries_count} queries, k={k}\n")
    print(f"{'dim':>5}{'kd-tree':>12}{'brute (np)':>13}{'winner':>18}")
    for dim in (2, 4, 8, 16, 32):
        data = rng.normal(size=(n, dim))
        probes = rng.normal(size=(queries_count, dim))

        tree = ImplicitKdTree(data)
        t0 = time.perf_counter()
        tree_hits = [tree.k_nearest(p, k) for p in probes]
        t_tree = (time.perf_counter() - t0) / queries_count

        t0 = time.perf_counter()
        idx, _ = brute_force_knn(data, probes, k)
        t_brute = (time.perf_counter() - t0) / queries_count

        # Both are exact, so they must agree exactly.
        assert [h[0] for h in tree_hits[0]] == idx[0].tolist()
        winner = "kd-tree" if t_tree < t_brute else "brute force"
        ratio = max(t_tree, t_brute) / min(t_tree, t_brute)
        print(
            f"{dim:>5}{t_tree * 1e3:>10.2f}ms{t_brute * 1e3:>11.2f}ms"
            f"{winner + f' {ratio:.0f}x':>18}"
        )

    print("\nApproximate search: 5,000 points in 64 dimensions, k=10")
    data = rng.normal(size=(5_000, 64))
    probes = rng.normal(size=(50, 64))
    truth, _ = brute_force_knn(data, probes, k)

    t0 = time.perf_counter()
    index = HNSW(data, m=16, ef_construction=100, seed=7)
    print(f"  HNSW build: {time.perf_counter() - t0:.1f}s")
    for ef in (20, 50, 150):
        t0 = time.perf_counter()
        hits = [index.query(p, k, ef=ef) for p in probes]
        elapsed = time.perf_counter() - t0
        recall = sum(
            len({i for i, _ in h} & set(t.tolist())) for h, t in zip(hits, truth)
        ) / (len(probes) * k)
        print(
            f"  ef={ef:>3}  {elapsed / len(probes) * 1e3:6.2f}ms/query  recall={recall:.3f}"
        )

    tree = ImplicitKdTree(data)
    t0 = time.perf_counter()
    for p in probes[:10]:
        tree.k_nearest(p, k)
    print(
        f"  exact kd-tree:     {(time.perf_counter() - t0) / 10 * 1e3:6.2f}ms/query "
        f"(recall 1.000, but no better than a scan at this dimension)"
    )
