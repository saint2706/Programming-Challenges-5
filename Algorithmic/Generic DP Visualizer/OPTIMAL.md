# Optimal Solution: Generic DP Visualizer

**Challenge:** build a tool that takes a DP table and a recurrence, and steps
through filling it in.

**Short answer:** the existing implementation animates the 0/1 knapsack table.
That is a demonstration of _one_ DP, not a generic tool — nothing about it
transfers to edit distance or matrix chain multiplication. What generalises is
the **dependency graph**, and once a DP is expressed as one, the tool can do
considerably more than animate it: it can _derive_ the space optimisation and
_detect_ the asymptotic speedups that are normally applied by hand.
Implementation: [`optimal_dp.py`](optimal_dp.py).

---

## 1. The right abstraction

Every dynamic program is exactly two things:

1. A **DAG over states** — which states each state needs.
2. A **combining rule** — how a state's value follows from its dependencies'.

Take those separately and declaratively:

```python
DP(
    dependencies = lambda state: [...],       # what it needs
    combine      = lambda state, values: ..., # how to fold them
    base         = lambda state: ... or None, # base cases
)
```

Keeping `dependencies` separate from `combine` is the design decision that makes
everything else possible: **the dependency structure can be walked without
evaluating anything**, so the DAG becomes a first-class object to analyse rather
than an implicit consequence of a recursive function's control flow.

Evaluation is then two iterative passes — discover the reachable DAG, sort it
topologically, evaluate in order. Two properties fall out for free:

- **No recursion limit.** A memoised recursive DP dies at ~1000 states of depth.
  This handles a 20 000-deep chain; the test suite pins it.
- **Cycles are reported, not crashed into.** A cyclic recurrence produces
  `ValueError: the dependency graph contains a cycle; (3, 2) is on or after it`
  rather than a `RecursionError` traceback with no indication of where.

## 2. What the tool derives that a visualiser normally cannot

### The rolling-array optimisation, derived rather than remembered

"You only need two rows" for edit distance is a thing every programmer
eventually memorises, per problem. It is not folklore — it is a **computable
property of the dependency stencil**. If every edge moves at most `w` steps back
along dimension `i`, then exactly `w+1` layers of that dimension need to be live.

Running it on edit distance:

```
stencil          (0, 1), (1, 0), (1, 1)
space            roll dimension 1: keep 2 layer(s) instead of 8 -> 4x less memory
```

On 0/1 knapsack with 40 items and capacity 200:

```
stencil          (1, 0), (1, 1), (1, 2), (1, 3), (1, 5), (1, 9), ...
space            roll dimension 0: keep 2 layer(s) instead of 41 -> 20x less memory
```

Both are the textbook answers — the two-row edit distance DP and the
one-dimensional knapsack array — **obtained by inspecting the trace**, with the
tool also picking which dimension is better to roll. Nobody had to recognise the
pattern.

The analysis is careful about the case that breaks it: if any edge reaches
_forward_ along a dimension, that dimension cannot be rolled in the natural
direction, and the analysis reports the full extent rather than a wrong window.

### The critical path, which bounds parallelism before you write any

The longest chain of dependencies is a hard floor on how long any parallel
implementation can take. Comparing it against the state count answers "is
parallelising worth attempting?" before any parallel code exists.

| DP                           | States | Critical path | Peak width |        Best possible speedup |
| :--------------------------- | -----: | ------------: | ---------: | ---------------------------: |
| Edit distance (6×7)          |     56 |            13 |         14 |                         4.3× |
| Knapsack (40 items, cap 200) |  6 700 |            41 |        201 |                     **163×** |
| A pure chain                 |    101 |           101 |          1 | **1.0×** — never parallelise |

The knapsack number is the useful one: 163× available parallelism, with 201
states ready at once, says a wavefront implementation is worth writing. The
chain says the opposite, unambiguously.

## 3. Detecting asymptotic speedups

Two classical DP optimisations turn on the same hypothesis, the **quadrangle
inequality** (Monge condition): for all `a ≤ b ≤ c ≤ d`,

$$w(a,c) + w(b,d) \le w(a,d) + w(b,c)$$

When it holds, the argmin of the DP is monotone, and the inner loop can be
restricted to a range that telescopes.

`satisfies_quadrangle_inequality` checks it — exhaustively for small `n`,
by sampling above that. **This check matters more than it looks**: applying
Knuth's optimisation when the hypothesis fails produces a _wrong answer_, not a
slow one. Silent wrongness is exactly the failure mode a tool should catch.

Measured, with both versions verified to return identical answers:

| Recurrence                   |               Naive |                       Optimised | Speedup |
| :--------------------------- | ------------------: | ------------------------------: | ------: |
| Interval DP, `n = 260`       |    268.9 ms `O(n³)` |     **33.1 ms** `O(n²)` (Knuth) |      8× |
| Layered DP, 1 500 × 8 layers | 1 523.8 ms `O(kn²)` | **26.1 ms** `O(kn log n)` (D&C) | **58×** |

### A correctness trap worth recording

The first version of `divide_and_conquer_dp` implemented the one-dimensional
recurrence `dp[i] = min_{j<i} (dp[j] + cost(j,i))`. That is wrong, and the
reason is subtle: divide and conquer computes the _midpoint first_, so it reads
`dp[j]` values for `j < mid` that have not been computed yet.

The technique requires every candidate value to be **final before the layer
starts** — which is why it is always presented over a layered recurrence
`dp[k][i] = min_j (dp[k-1][j] + cost(j,i))`. The API now takes the previous
layer explicitly, so the precondition is impossible to violate by accident. The
genuinely online case needs SMAWK or LARSCH instead, which is a much heavier
construction.

The bug was caught by comparing against the naive implementation on random
inputs, which is why both naive versions are kept rather than deleted.

## 4. The visualiser

`render_html` writes a standalone animated page for any DP whose states are
integer pairs — which covers most table-shaped DPs. Each step highlights the
cell being computed **and the cells it read**, so the recurrence is visible
rather than described. The page is self-contained: no CDN, no external styles,
theme-aware, with play/step/reset and a speed control.

Being generic is the point. The same call renders edit distance, LCS, knapsack,
or a DP written five minutes ago, because it works from the trace rather than
from knowledge of the problem.

## 5. Non-optimal alternatives, and why each loses

| Alternative                                                      | Verdict                                                                                                                                                                                                                                                                                                                                                                            |
| :--------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hard-coded per-problem visualiser** (the current `dpLogic.js`) | What is here today. Correct and clear for knapsack; zero transfer to any other DP, and it can say nothing about the DP's structure because the structure is baked into the code rather than represented.                                                                                                                                                                           |
| **Recurrence as a string, `eval`-ed**                            | The current `dpLogic.js` approach (`"dp[i-1][j] + dp[i][j-1] + 1"`). Genuinely generic over grid DPs, and its dependency extraction is a real feature. But it is limited to grids indexed by `i`/`j`, needs a parser or `eval`, and cannot express a DP over strings, sets, or bitmasks. Passing functions is both simpler and strictly more general.                              |
| **Memoised recursion with a tracing decorator**                  | The obvious way to capture dependencies: wrap the recursive call, record who asked. Works, and gives a nicer API — one function instead of two. Two real costs: it dies at ~1000 states of recursion depth, and the dependency graph only exists _after_ evaluation, so nothing can be analysed or reordered beforehand. Explicit dependencies trade a little ergonomics for both. |
| **Full table fill, bottom-up**                                   | Simplest possible engine, and often fastest. Evaluates states that are never needed — the knapsack example above reaches only 46 of ~1200 states from one target — and requires the caller to already know a valid evaluation order, which is the thing the tool should be deriving.                                                                                               |
| **A DP DSL with its own syntax**                                 | More expressive notation, at the cost of a parser, an evaluator, and a language for users to learn. Python functions are already a perfectly good DSL for this.                                                                                                                                                                                                                    |
| **Symbolic analysis of the recurrence** (SymPy, AST inspection)  | Could derive the stencil without running the DP, and handle unbounded state spaces. Substantially harder, and it fails exactly where DPs get interesting — data-dependent dependencies, like LCS branching on whether two characters match. Tracing handles that for free because it observes what actually happened.                                                              |
| **Manual complexity analysis**                                   | What everyone does. Correct when done carefully, and the failure mode is silent: a missed rolling-array opportunity is invisible, and a wrongly-applied Knuth optimisation returns a plausible wrong number. Both are exactly what a tool should catch.                                                                                                                            |

### Deliberately not implemented

**SMAWK** (`O(n)` row minima of a totally monotone matrix) and **LARSCH** (its
online variant) close the remaining gap: they handle the one-dimensional
recurrence that divide and conquer cannot. They are the genuinely optimal
algorithms for that shape and are noticeably more intricate than everything
here; the layered form covers the common cases and its precondition is
enforceable, which the online form's is not.

**Automatic application** of the detected optimisations. The tool reports that a
rolling array would save 20× and that Knuth's optimisation applies; it does not
rewrite the DP to use them. Detection is the hard and useful part —
mechanically applying a known-valid transformation is comparatively routine, and
doing it silently would hide the analysis that motivated it.

## 6. Complexity summary

| Operation                           | Cost                                         |
| :---------------------------------- | :------------------------------------------- |
| `DP.solve`                          | `O(V + E)` beyond the user's `combine` calls |
| `analyze`                           | `O(V + E)`                                   |
| `satisfies_quadrangle_inequality`   | `O(n⁴)` exhaustive, `O(sample)` sampled      |
| `naive_interval_dp`                 | `O(n³)`                                      |
| `knuth_interval_dp`                 | `O(n²)`                                      |
| `divide_and_conquer_dp` (one layer) | `O(n log n)`                                 |
| `render_html`                       | `O(V + E)`                                   |

---

## References

- Knuth, _Optimum binary search trees_, Acta Informatica 1(1), 1971. (The original optimisation.)
- Yao, _Efficient dynamic programming using quadrangle inequalities_, STOC 1980. (The general condition.)
- Aggarwal, Klawe, Moran, Shor, Wilber, _Geometric applications of a matrix-searching algorithm_, Algorithmica 2, 1987. (SMAWK.)
- Larmore & Schieber, _On-line dynamic programming with applications to the prediction of RNA secondary structure_, J. Algorithms 12, 1991. (LARSCH.)
- Galil & Park, _Dynamic programming with convexity, concavity and sparsity_, Theoretical Computer Science 92, 1992. (The survey that maps this space.)
