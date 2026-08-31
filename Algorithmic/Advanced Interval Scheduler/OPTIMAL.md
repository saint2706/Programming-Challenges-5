# Optimal Solution: Advanced Interval Scheduler

**Challenge:** given `n` weighted intervals, select a pairwise non-overlapping
subset of maximum total weight.

**Short answer:** the textbook `O(n log n)` DP does `n` binary searches it does
not need. A single **left-to-right event sweep** computes the same table with
one sort and one linear pass; with a radix sort over integer endpoints the whole
algorithm is `O(n)`, which is optimal in the strongest sense — you cannot read
the input in less. Implementation: [`optimal_scheduler.py`](optimal_scheduler.py).

---

## 1. The problem and the standard solution

Sort intervals by finish time. Let `p(j)` be the largest index `i < j` whose
interval is compatible with `j` (`fᵢ ≤ sⱼ`). Then

$$OPT(j) = \max\big(w_j + OPT(p(j)),\; OPT(j-1)\big)$$

The usual implementation computes each `p(j)` with a binary search over the
finish times. That is `O(n log n)` for the sort **plus** `O(n log n)` for the
searches — the logarithm appears twice, and the second one is avoidable.

## 2. The optimal algorithm: one event sweep

Split each interval into two events, an END at `fⱼ` and a START at `sⱼ`, and
sort all `2n` of them together, ties broken **END before START**. Sweep left to
right maintaining one running value:

> `best` = the maximum total weight achievable using only intervals that have
> already _finished_.

Then the entire DP is two lines:

- **At the START of `j`:** `best` is, by definition, `OPT(p(j))` — the best
  achievable using only intervals compatible with `j`. Record it as
  `value_if_taken[j]`, and record the interval that achieved it as `j`'s
  predecessor. **No search is needed: the sweep has already walked past exactly
  the right prefix.**
- **At the END of `j`:** `j`'s own best chain is worth
  `value_if_taken[j] + wⱼ`. Fold it into `best`.

The answer is the final `best`; the schedule comes from following predecessor
links backwards. The binary searches are gone, replaced by `2n` sequential
steps that the sort was going to make us pay for anyway.

The END-before-START tie-break is what makes half-open intervals work: `[1,5)`
and `[5,9)` are compatible, so at coordinate 5 the first must be folded into
`best` before the second reads it.

### Why this matters beyond constant factors

The sweep makes the running time `O(sort(n)) + O(n)`. **All** of the remaining
cost is in the sort, which means any faster sort immediately makes the whole
algorithm faster — a leverage the binary-search version does not have, since its
searches are irreducibly `Θ(n log n)` regardless of how the input arrives.

That is what `schedule_integer_endpoints` exploits. Endpoints in real scheduling
problems are integers — timestamps, slot indices, seconds since epoch — so a
radix sort applies and the total becomes **`O(n)`**. The
`Ω(n log n)` bound that people quote for this problem is a _comparison-model_
bound; integer endpoints leave that model, and the sweep is what lets you cash
that in.

## 3. Measured results, including one that contradicts the theory

200 000 random intervals, CPython 3.11:

| Implementation                        |       Time |    vs. textbook |
| :------------------------------------ | ---------: | --------------: |
| Sweep, NumPy sort (`schedule_arrays`) | **0.20 s** | **5.3× faster** |
| Sweep, packed-int sort (`schedule`)   |     0.87 s |     1.2× faster |
| Textbook binary-search DP             |     1.06 s |            1.0× |
| Sweep, pure-Python radix sort         |     1.07 s |            1.0× |

Two findings worth stating plainly:

**The linear-time algorithm is the slowest one here.** A pure-Python radix sort
is interpreted bytecode competing against `list.sort`, which is C Timsort. The
~3× constant-factor handicap swamps the asymptotic win for any `n` that fits in
a Python process. This is the honest result, and it is why
`schedule_integer_endpoints` is documented as the algorithmically optimal
variant rather than advertised as the fast one. In a compiled language the
ranking inverts.

**Where the real Python win is: move the sort into C.** The sweep's sequential
dependency cannot be vectorised — each `OPT(p(j))` is read off a running maximum
that later steps update. But the sort can be, and after the sweep removes the
binary searches, the sort is _all_ that is left of the superlinear work. Packing
each event into a single `int64` (`coordinate << k | kind << (k-1) | index`)
means NumPy can sort them in C, giving the 5.3×. Packing also helps pure Python
by about 2×, because sorting machine integers needs no `key` function and no
tuple comparisons.

## 4. The generalisation the title implies: `k` machines

With `k` parallel machines the problem stops being a chain and becomes a flow.
Neither greedy nor the one-machine DP extends — there is no "last compatible
interval" when `k` intervals may be in flight.

**The reduction** (`schedule_k_machines`): compress endpoints onto a line and
build a path graph over them, consecutive positions joined by edges of capacity
`k` and cost 0. Add, for each interval, an edge from its start position to its
end position with capacity 1 and cost `−wⱼ`. Push `k` units from leftmost to
rightmost at minimum cost.

Each unit of flow is one machine's timeline; an interval edge carrying flow is a
scheduled interval; capacity `k` on the path edges is exactly the constraint
that no instant is oversubscribed. Negative costs mean minimum cost maximises
weight, and the solver stops augmenting once paths stop being profitable — so it
selects the best subset rather than being forced to fill every machine.

Costs are negative, so the first potential pass exploits the fact that the
initial graph is a DAG in coordinate order (exact distances by relaxing in index
order); after that, Johnson potentials keep reduced costs non-negative and
Dijkstra applies. `O(k · E log V)` with `V, E = O(n)`.

## 5. The unweighted special case

If all weights are equal, drop the DP: repeatedly take the interval with the
**earliest finish time**. Optimal by an exchange argument — swapping in the
earliest-finishing compatible interval never blocks anything the replaced one
allowed, so any optimal solution can be transformed into the greedy one without
shrinking.

This is worth knowing precisely because it fails the moment weights differ.
`[(0,10,100), (0,1,1), (2,3,1)]` gives greedy 2 and the DP 100 — the ratio is
unbounded. The test suite pins both halves of this.

## 6. Non-optimal alternatives, and why each loses

| Alternative                                                   | Verdict                                                                                                                                                                                                                                                    |
| :------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Binary-search DP** (textbook, and the current `main.py`)    | Correct and the same asymptotic class. Does `n` binary searches the sweep proves unnecessary, and cannot benefit from integer-sorting. Kept in the module as an independent cross-check for the tests.                                                     |
| **Earliest-finish greedy**                                    | Optimal for equal weights, unboundedly bad otherwise. See above.                                                                                                                                                                                           |
| **Largest-weight-first greedy**                               | Also unboundedly bad: one weight-10 interval blocking two weight-9 intervals gives 10 against an optimum of 18.                                                                                                                                            |
| **Shortest-interval-first greedy**                            | Bad in both directions — ignores weight entirely, and a short low-weight interval can split a long high-weight one out of the solution.                                                                                                                    |
| **Interval graph MIS via general max-weight independent set** | Correct (interval graphs are perfect, so MIS is polynomial) but wildly more expensive. The DP _is_ the specialised algorithm; going through general MIS machinery discards the linear structure that makes it easy.                                        |
| **ILP / branch-and-bound**                                    | Correct, exponential in the worst case, and unnecessary: the LP relaxation of this problem is integral, so an LP solver would find the DP's answer — slowly. The right tool for _variants_ the DP cannot express (precedences, setup times), not for this. |
| **Segment tree over `OPT`**                                   | Sometimes proposed to "speed up" the predecessor lookup. It is strictly worse: `O(log n)` per query with a much larger constant, to replace a binary search that the sweep removes for free.                                                               |
| **Memoised recursion on `OPT(j)`**                            | Same complexity, but adds Python recursion overhead and a stack-depth limit at a few thousand intervals. The iterative sweep has neither.                                                                                                                  |

### Deliberately not implemented

**Online / competitive interval scheduling.** If intervals arrive one at a time
and must be accepted or rejected irrevocably, no deterministic algorithm is
competitive at all — an adversary offers a weight-1 interval and then, if you
take it, a conflicting weight-`M` one. Bounded competitive ratios need extra
assumptions (bounded weight ratio, known interval lengths, or randomisation).
The problem as posed is offline, so this is out of scope, but it is the first
thing that breaks if the requirements change.

## 7. Design decision: empty intervals

An interval with `start == end` covers no point, so it conflicts with nothing
and every one with positive weight belongs in the optimal solution. All entry
points set them aside and add them back.

This is not only a semantic choice — it is a correctness requirement for the
sweep. An empty interval's END event sorts _before_ its own START event, so at
its START the running `best` can already include the interval itself, recording
it as its own predecessor and turning the backtracking walk into an infinite
loop. Handling empties separately is the clean fix; the test suite pins it.

## 8. Complexity summary

| Function                     | Time             | Space        | Notes                                 |
| :--------------------------- | :--------------- | :----------- | :------------------------------------ |
| `schedule`                   | `O(n log n)`     | `O(n)`       | One sort + one linear pass            |
| `schedule_arrays`            | `O(n log n)`     | `O(n)`       | Sort runs in C; 5× faster in practice |
| `schedule_integer_endpoints` | **`O(n)`**       | `O(n + 2^b)` | Optimal; slower in CPython            |
| `schedule_binary_search`     | `O(n log n)`     | `O(n)`       | Textbook; cross-check                 |
| `max_intervals`              | `O(n log n)`     | `O(n)`       | Unweighted only                       |
| `schedule_k_machines`        | `O(k · n log n)` | `O(n)`       | Min-cost flow                         |

---

## References

- Kleinberg & Tardos, _Algorithm Design_, §6.1. (The textbook DP.)
- Cormen, Leiserson, Rivest, Stein, _Introduction to Algorithms_, §16.1. (Unweighted greedy and its exchange argument.)
- Arkin & Silverberg, _Scheduling jobs with fixed start and end times_, Discrete Applied Mathematics 18 (1987). (The min-cost flow reduction for `k` machines.)
- Bar-Noy, Guha, Naor, Schieber, _Approximating the throughput of multiple machines in real-time scheduling_, SIAM J. Comput. 31 (2001). (What happens when the model gets harder.)
