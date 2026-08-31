"""A generic dynamic-programming engine that analyses and visualises any DP.

The existing visualisation in this directory animates the 0/1 knapsack table.
That is a demonstration of one DP, not a *generic* DP visualiser: nothing about
it transfers to edit distance, matrix chain multiplication, or a DP over an
irregular state space.

What generalises is the **dependency graph**. Every dynamic program is a DAG
over states plus a rule for combining a state's dependencies into its value.
Given those two things declaratively, this module:

* evaluates the DP iteratively, with no recursion limit
  (:class:`DP`, :class:`Solution`);
* derives properties of the DAG that are usually worked out by hand
  (:func:`analyze`) --

  - the **minimal rolling-window size** per dimension, which is exactly the
    space optimisation people rediscover per problem ("you only need two rows");
  - the **critical path**, which is the parallel depth and therefore a hard
    lower bound on how much parallelism can ever help;
  - the **peak width**, which is how much parallelism is actually available;

* tests whether an asymptotic speedup applies (:func:`satisfies_quadrangle_
  inequality`), and implements the two it unlocks -- Knuth's optimisation
  (`O(n^3)` to `O(n^2)`) and divide-and-conquer optimisation (`O(n^2)` to
  `O(n log n)`);
* renders the evaluation as a standalone animated HTML page
  (:func:`render_html`), which works for any DP whose states are integer pairs.

The interesting claim is the third one. The rolling-array trick and the
Knuth/divide-and-conquer speedups are normally applied by a human who has
recognised the pattern. Both are **decidable from the trace and the cost
function**, so the tool can recognise them instead. See ``OPTIMAL.md``.
"""

from __future__ import annotations

import html
import json
from collections import deque
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Hashable,
    List,
    Optional,
    Sequence,
    Tuple,
)

__all__ = [
    "DP",
    "Solution",
    "DPAnalysis",
    "analyze",
    "satisfies_quadrangle_inequality",
    "naive_interval_dp",
    "knuth_interval_dp",
    "divide_and_conquer_dp",
    "render_html",
    "knapsack",
    "edit_distance",
    "longest_common_subsequence",
]

State = Hashable


# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Solution:
    """The result of evaluating a DP, including everything needed to analyse it."""

    #: Computed value for every reachable state.
    values: Dict[State, Any]
    #: ``state -> the states it directly depends on``.
    dependencies: Dict[State, Tuple[State, ...]]
    #: Evaluation order actually used (a topological order of the DAG).
    order: Tuple[State, ...]
    #: The states the caller asked for.
    targets: Tuple[State, ...]

    def value(self, state: State) -> Any:
        """Return the computed value of ``state``.

        Raises:
            KeyError: If the state was not reachable from any target.
        """
        return self.values[state]

    @property
    def state_count(self) -> int:
        """Number of distinct states evaluated."""
        return len(self.values)

    @property
    def edge_count(self) -> int:
        """Number of dependency edges -- the DP's real work."""
        return sum(len(deps) for deps in self.dependencies.values())


class DP:
    """A dynamic program described declaratively, then evaluated and analysed.

    A DP is fully specified by three functions:

    * ``dependencies(state)`` -- which states this one needs. Return an empty
      sequence for a base case.
    * ``combine(state, values)`` -- the value, given the dependencies' values in
      the same order ``dependencies`` returned them.
    * ``base(state)`` -- optional shortcut returning a value directly for base
      cases, so ``combine`` never sees them.

    Splitting "what does it depend on" from "how is it combined" is what makes
    the analysis possible: the dependency structure can be walked without
    evaluating anything, and the resulting DAG is a first-class object.

    Evaluation is a two-pass iterative process -- discover the reachable DAG,
    then evaluate in topological order. There is no recursion, so DP chains of
    any depth work without touching the recursion limit.

    Example:
        >>> fib = DP(
        ...     dependencies=lambda n: () if n < 2 else (n - 1, n - 2),
        ...     combine=lambda n, vals: sum(vals),
        ...     base=lambda n: n if n < 2 else None,
        ... )
        >>> fib.solve(30).value(30)
        832040
    """

    def __init__(
        self,
        dependencies: Callable[[State], Sequence[State]],
        combine: Callable[[State, Sequence[Any]], Any],
        base: Optional[Callable[[State], Any]] = None,
    ) -> None:
        """Create a DP.

        Args:
            dependencies: Maps a state to the states it needs.
            combine: Maps a state and its dependencies' values to its value.
            base: Optional; returns a value for base states and ``None`` for
                states that should be computed by ``combine``.
        """
        self._dependencies = dependencies
        self._combine = combine
        self._base = base

    def solve(self, *targets: State) -> Solution:
        """Evaluate the DP for the given target states.

        Args:
            *targets: The states whose values are wanted. Only states reachable
                from these are evaluated.

        Returns:
            A :class:`Solution`.

        Raises:
            ValueError: If the dependency graph contains a cycle. (This is the
                error a recursive memoised implementation reports as infinite
                recursion, which is far harder to diagnose.)
        """
        graph: Dict[State, Tuple[State, ...]] = {}
        stack = list(targets)
        while stack:
            state = stack.pop()
            if state in graph:
                continue
            if self._base is not None and self._base(state) is not None:
                graph[state] = ()
                continue
            deps = tuple(self._dependencies(state))
            graph[state] = deps
            stack.extend(d for d in deps if d not in graph)

        order = _topological_order(graph)
        values: Dict[State, Any] = {}
        for state in order:
            if self._base is not None:
                seeded = self._base(state)
                if seeded is not None:
                    values[state] = seeded
                    continue
            deps = graph[state]
            values[state] = self._combine(state, [values[d] for d in deps])

        return Solution(
            values=values,
            dependencies=graph,
            order=tuple(order),
            targets=tuple(targets),
        )


def _topological_order(graph: Dict[State, Tuple[State, ...]]) -> List[State]:
    """Kahn's algorithm over ``state -> dependencies``, dependencies first.

    Raises:
        ValueError: If the graph has a cycle, naming a state on it.
    """
    dependents: Dict[State, List[State]] = {state: [] for state in graph}
    remaining: Dict[State, int] = {}
    for state, deps in graph.items():
        remaining[state] = len(deps)
        for dep in deps:
            dependents[dep].append(state)

    queue = deque(state for state, count in remaining.items() if count == 0)
    order: List[State] = []
    while queue:
        state = queue.popleft()
        order.append(state)
        for dependent in dependents[state]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(graph):
        stuck = next(s for s, count in remaining.items() if count > 0)
        raise ValueError(
            f"the dependency graph contains a cycle; {stuck!r} is on or after it"
        )
    return order


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DPAnalysis:
    """Structural properties derived from a solved DP's dependency graph."""

    states: int
    edges: int
    #: Longest chain of dependencies. No amount of parallelism beats this.
    critical_path: int
    #: Largest number of states that could be evaluated simultaneously.
    peak_width: int
    #: For grid-shaped states: the distinct dependency offsets observed.
    stencil: Tuple[Tuple[int, ...], ...] = ()
    #: Per dimension, how many layers must be kept live. ``None`` if the states
    #: are not integer tuples, or a dimension has unbounded look-back.
    rolling_window: Optional[Tuple[int, ...]] = None
    #: Per dimension, the number of distinct coordinate values.
    extent: Optional[Tuple[int, ...]] = None

    @property
    def parallel_speedup_bound(self) -> float:
        """Best possible speedup from unlimited parallelism (work over depth)."""
        return self.states / self.critical_path if self.critical_path else 1.0

    def space_saving(self) -> Optional[Tuple[int, float]]:
        """Best single-dimension rolling-array optimisation available.

        Returns:
            ``(dimension, factor)`` where ``factor`` is how many times less
            memory the rolling version needs, or ``None`` if the states are not
            grid-shaped or nothing can be rolled.
        """
        if self.rolling_window is None or self.extent is None:
            return None
        best: Optional[Tuple[int, float]] = None
        for axis, (window, size) in enumerate(zip(self.rolling_window, self.extent)):
            if window >= size:
                continue
            factor = size / window
            if best is None or factor > best[1]:
                best = (axis, factor)
        return best

    def summary(self) -> str:
        """A human-readable report of everything derived."""
        lines = [
            f"states           {self.states:,}",
            f"edges            {self.edges:,}",
            f"critical path    {self.critical_path:,}  "
            f"(sequential depth; parallelism cannot beat this)",
            f"peak width       {self.peak_width:,}  (states evaluable at once)",
            f"parallel bound   {self.parallel_speedup_bound:.1f}x speedup at best",
        ]
        if self.stencil:
            offsets = ", ".join(str(tuple(o)) for o in self.stencil[:8])
            more = " ..." if len(self.stencil) > 8 else ""
            lines.append(f"stencil          {offsets}{more}")
        saving = self.space_saving()
        if saving is not None:
            axis, factor = saving
            window = self.rolling_window[axis]  # type: ignore[index]
            lines.append(
                f"space            roll dimension {axis}: keep {window} layer(s) "
                f"instead of {self.extent[axis]} -> {factor:.0f}x less memory"  # type: ignore[index]
            )
        elif self.rolling_window is not None:
            lines.append("space            no rolling-array optimisation available")
        return "\n".join(lines)


def analyze(solution: Solution) -> DPAnalysis:
    """Derive structural properties from a solved DP.

    The two facts worth highlighting:

    **The rolling window is decidable, not a trick.** If every dependency edge
    moves at most `w` steps back along dimension `i`, then only `w+1` layers of
    that dimension need to be live at once. "You only need two rows" for edit
    distance is exactly this computation with `w = 1`, and it falls out of the
    trace rather than requiring the reader to spot it.

    **The critical path is a hard limit.** It is the longest chain of
    dependencies, so no parallel implementation can finish in fewer than that
    many sequential steps. Comparing it against the state count says whether
    parallelising is worth attempting at all before any is written.

    Args:
        solution: A solved DP.

    Returns:
        A :class:`DPAnalysis`.
    """
    graph = solution.dependencies
    # Longest path and level assignment, in the topological order already known.
    depth: Dict[State, int] = {}
    for state in solution.order:
        deps = graph.get(state, ())
        depth[state] = 1 + max((depth[d] for d in deps), default=0)

    level_counts: Dict[int, int] = {}
    for value in depth.values():
        level_counts[value] = level_counts.get(value, 0) + 1

    stencil: Tuple[Tuple[int, ...], ...] = ()
    rolling: Optional[Tuple[int, ...]] = None
    extent: Optional[Tuple[int, ...]] = None

    grid_states = [s for s in graph if _is_integer_tuple(s)]
    if grid_states and len(grid_states) == len(graph):
        dims = len(grid_states[0])
        if all(len(s) == dims for s in grid_states):
            offsets = set()
            bounded = True
            for state, deps in graph.items():
                for dep in deps:
                    offset = tuple(a - b for a, b in zip(state, dep))
                    if any(o < 0 for o in offset):
                        # Dependencies that reach *forward* rule out rolling
                        # that dimension in the natural direction.
                        bounded = False
                    offsets.add(offset)
            stencil = tuple(sorted(offsets))
            extent = tuple(len({s[axis] for s in grid_states}) for axis in range(dims))
            if bounded and offsets:
                rolling = tuple(
                    max(o[axis] for o in offsets) + 1 for axis in range(dims)
                )
            else:
                rolling = tuple(extent)

    return DPAnalysis(
        states=solution.state_count,
        edges=solution.edge_count,
        critical_path=max(depth.values(), default=0),
        peak_width=max(level_counts.values(), default=0),
        stencil=stencil,
        rolling_window=rolling,
        extent=extent,
    )


def _is_integer_tuple(state: State) -> bool:
    """True if ``state`` is a tuple of plain ints (a grid coordinate)."""
    return isinstance(state, tuple) and all(
        isinstance(x, int) and not isinstance(x, bool) for x in state
    )


# --------------------------------------------------------------------------
# Asymptotic speedups, and detecting when they apply
# --------------------------------------------------------------------------


def satisfies_quadrangle_inequality(
    cost: Callable[[int, int], float], n: int, sample: Optional[int] = None
) -> bool:
    """Test whether ``cost`` obeys the quadrangle inequality on ``[0, n)``.

    The condition is, for all ``a <= b <= c <= d``::

        cost(a, c) + cost(b, d) <= cost(a, d) + cost(b, c)

    It is the hypothesis of both speedups below. When it holds, the argmin of an
    interval DP is monotone in both endpoints, which is what lets Knuth's
    optimisation restrict the inner loop to a range that telescopes to `O(n^2)`
    total work instead of `O(n^3)`.

    Being able to *check* this matters: the condition is easy to state and easy
    to get wrong by eye, and applying Knuth's optimisation when it does not hold
    silently produces wrong answers rather than slow ones.

    Args:
        cost: The cost function, defined for ``0 <= i <= j < n``.
        n: Size of the index range.
        sample: If given, check this many random quadruples instead of all of
            them. Exhaustive checking is `O(n^4)`; use a sample above `n = 30`.

    Returns:
        ``True`` if no violation was found. With ``sample`` set this is
        evidence, not proof.
    """
    if n < 2:
        return True
    if sample is None:
        for a in range(n):
            for b in range(a, n):
                for c in range(b, n):
                    for d in range(c, n):
                        if cost(a, c) + cost(b, d) > cost(a, d) + cost(b, c) + 1e-9:
                            return False
        return True

    import random

    rng = random.Random(0)
    for _ in range(sample):
        quad = sorted(rng.randrange(n) for _ in range(4))
        a, b, c, d = quad
        if cost(a, c) + cost(b, d) > cost(a, d) + cost(b, c) + 1e-9:
            return False
    return True


def naive_interval_dp(n: int, cost: Callable[[int, int], float]) -> float:
    """Interval DP by brute force: `O(n^3)`.

    Solves ``dp[i][j] = min over i<k<j of (dp[i][k] + dp[k][j]) + cost(i, j)``,
    the shape shared by matrix-chain multiplication, optimal binary search
    trees, and file-merging problems.

    Args:
        n: Number of boundary positions; intervals run over ``[0, n-1]``.
        cost: Cost of the interval ``(i, j)``.

    Returns:
        ``dp[0][n-1]``.
    """
    if n < 2:
        return 0.0
    dp = [[0.0] * n for _ in range(n)]
    for width in range(2, n):
        for i in range(n - width):
            j = i + width
            dp[i][j] = min(dp[i][k] + dp[k][j] for k in range(i + 1, j)) + cost(i, j)
    return dp[0][n - 1]


def knuth_interval_dp(n: int, cost: Callable[[int, int], float]) -> float:
    """The same interval DP in `O(n^2)`, via Knuth's optimisation.

    When ``cost`` satisfies the quadrangle inequality and is monotone on
    intervals, the optimal split point is monotone::

        opt[i][j-1] <= opt[i][j] <= opt[i+1][j]

    so the inner loop over ``k`` can be restricted to that range. The bounds
    telescope: summing the range lengths over a diagonal gives `O(n)` per
    diagonal and `O(n^2)` overall.

    **Check the hypothesis first** with :func:`satisfies_quadrangle_inequality`.
    If it does not hold, this returns a wrong answer, not a slow one.

    Args:
        n: Number of boundary positions.
        cost: Cost of the interval ``(i, j)``. Must satisfy the quadrangle
            inequality.

    Returns:
        ``dp[0][n-1]``.
    """
    if n < 2:
        return 0.0
    dp = [[0.0] * n for _ in range(n)]
    opt = [[0] * n for _ in range(n)]
    for i in range(n - 1):
        opt[i][i + 1] = i

    for width in range(2, n):
        for i in range(n - width):
            j = i + width
            lower = opt[i][j - 1]
            upper = opt[i + 1][j] if i + 1 < n else j - 1
            best = float("inf")
            best_k = lower
            for k in range(max(lower, i + 1), min(upper, j - 1) + 1):
                candidate = dp[i][k] + dp[k][j]
                if candidate < best:
                    best = candidate
                    best_k = k
            dp[i][j] = best + cost(i, j)
            opt[i][j] = best_k
    return dp[0][n - 1]


def divide_and_conquer_dp(
    previous: Sequence[float], cost: Callable[[int, int], float]
) -> List[float]:
    """One layer of ``next[i] = min over j <= i of (previous[j] + cost(j, i))``.

    The naive evaluation of a layer is `O(n^2)`. When the argmin is monotone in
    ``i`` -- guaranteed when ``cost`` satisfies the quadrangle inequality --
    divide and conquer applies: compute the middle element's optimum, which
    bounds the candidate range for everything to its left and right, and
    recurse. Each level does `O(n)` work over `O(log n)` levels, so a layer
    costs `O(n log n)`.

    **This is deliberately the layered form.** The one-dimensional recurrence
    ``dp[i] = min over j < i of (dp[j] + cost(j, i))`` looks like it should work
    the same way, and it does not: computing the midpoint first would read
    ``dp[j]`` values that have not been computed yet. The technique needs every
    candidate ``previous[j]`` to be final before the layer starts. (The truly
    online case needs SMAWK or the LARSCH algorithm instead, which is a
    different and considerably heavier construction.)

    Args:
        previous: The preceding layer, indexed ``0..n``.
        cost: ``cost(j, i)`` for ``j <= i``. Must satisfy the quadrangle
            inequality for the result to be correct.

    Returns:
        The next layer, same length as ``previous``.
    """
    n = len(previous) - 1
    if n < 0:
        return []
    nxt = [float("inf")] * (n + 1)

    def solve(lo: int, hi: int, opt_lo: int, opt_hi: int) -> None:
        """Fill next[lo..hi], knowing each argmin lies in [opt_lo, opt_hi]."""
        if lo > hi:
            return
        mid = (lo + hi) // 2
        best = float("inf")
        best_j = opt_lo
        for j in range(opt_lo, min(mid, opt_hi) + 1):
            candidate = previous[j] + cost(j, mid)
            if candidate < best:
                best = candidate
                best_j = j
        nxt[mid] = best
        # Monotonicity: everything left of mid has its argmin at or before
        # best_j, everything right of it at or after.
        solve(lo, mid - 1, opt_lo, best_j)
        solve(mid + 1, hi, best_j, opt_hi)

    solve(0, n, 0, n)
    return nxt


# --------------------------------------------------------------------------
# Ready-made dynamic programs
# --------------------------------------------------------------------------


def knapsack(weights: Sequence[int], values: Sequence[int], capacity: int) -> DP:
    """0/1 knapsack as a :class:`DP` over states ``(item_index, remaining)``."""
    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")

    def dependencies(state):
        i, remaining = state
        deps = [(i - 1, remaining)]
        if weights[i - 1] <= remaining:
            deps.append((i - 1, remaining - weights[i - 1]))
        return deps

    def combine(state, vals):
        i, _ = state
        if len(vals) == 1:
            return vals[0]
        return max(vals[0], vals[1] + values[i - 1])

    return DP(
        dependencies=dependencies,
        combine=combine,
        base=lambda state: 0 if state[0] == 0 else None,
    )


def edit_distance(a: str, b: str) -> DP:
    """Levenshtein distance as a :class:`DP` over states ``(i, j)``."""

    def dependencies(state):
        i, j = state
        return [(i - 1, j), (i, j - 1), (i - 1, j - 1)]

    def combine(state, vals):
        i, j = state
        up, left, diag = vals
        return min(up + 1, left + 1, diag + (0 if a[i - 1] == b[j - 1] else 1))

    def base(state):
        i, j = state
        if i == 0:
            return j
        if j == 0:
            return i
        return None

    return DP(dependencies=dependencies, combine=combine, base=base)


def longest_common_subsequence(a: str, b: str) -> DP:
    """LCS length as a :class:`DP` over states ``(i, j)``."""

    def dependencies(state):
        i, j = state
        if a[i - 1] == b[j - 1]:
            return [(i - 1, j - 1)]
        return [(i - 1, j), (i, j - 1)]

    def combine(state, vals):
        return vals[0] + 1 if len(vals) == 1 else max(vals)

    return DP(
        dependencies=dependencies,
        combine=combine,
        base=lambda state: 0 if state[0] == 0 or state[1] == 0 else None,
    )


# --------------------------------------------------------------------------
# Visualisation
# --------------------------------------------------------------------------


def render_html(
    solution: Solution,
    path: str,
    title: str = "Dynamic Programming Trace",
    max_steps: int = 4000,
) -> str:
    """Write a standalone animated HTML page showing the DP being filled in.

    Works for any DP whose states are pairs of integers -- which covers most
    table-shaped dynamic programs. Each step highlights the cell being computed
    and the cells it read, so the recurrence is visible rather than described.

    Args:
        solution: A solved DP whose states are ``(row, col)`` integer pairs.
        path: Where to write the HTML file.
        title: Page title.
        max_steps: Cap on animation steps, so a large DP still produces a
            usable page.

    Returns:
        The path written.

    Raises:
        ValueError: If the states are not integer pairs.
    """
    states = list(solution.order)
    if not all(_is_integer_tuple(s) and len(s) == 2 for s in states):
        raise ValueError(
            "render_html requires states that are (row, col) integer pairs"
        )

    rows = sorted({s[0] for s in states})
    cols = sorted({s[1] for s in states})
    row_index = {value: i for i, value in enumerate(rows)}
    col_index = {value: i for i, value in enumerate(cols)}

    steps = []
    for state in states[:max_steps]:
        deps = solution.dependencies.get(state, ())
        steps.append(
            {
                "r": row_index[state[0]],
                "c": col_index[state[1]],
                "v": _jsonable(solution.values[state]),
                "d": [
                    [row_index[d[0]], col_index[d[1]]]
                    for d in deps
                    if d[0] in row_index and d[1] in col_index
                ],
            }
        )

    analysis = analyze(solution)
    payload = json.dumps(
        {
            "rows": len(rows),
            "cols": len(cols),
            "rowLabels": rows,
            "colLabels": cols,
            "steps": steps,
            "truncated": len(states) > max_steps,
        }
    )

    document = _HTML_TEMPLATE.format(
        title=html.escape(title),
        summary=html.escape(analysis.summary()),
        payload=payload,
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return path


def _jsonable(value: Any) -> Any:
    """Coerce a DP value into something JSON can carry."""
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return str(value)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; --bg:#fbfbfa; --fg:#1a1a19; --line:#d6d4d0;
           --cell:#ffffff; --active:#2f6f4f; --dep:#c8842a; --done:#eef2ef; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#16171a; --fg:#e8e6e3; --line:#34363b; --cell:#1e2024;
             --active:#5fbf8f; --dep:#e0a458; --done:#23262b; }}
  }}
  body {{ margin:0; padding:24px; background:var(--bg); color:var(--fg);
          font:14px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif; }}
  h1 {{ font-size:18px; margin:0 0 4px; }}
  pre {{ background:var(--done); border:1px solid var(--line); border-radius:6px;
         padding:12px; overflow-x:auto; font-size:12px; }}
  .controls {{ display:flex; gap:8px; align-items:center; margin:16px 0; flex-wrap:wrap; }}
  button {{ font:inherit; padding:6px 14px; border:1px solid var(--line);
            border-radius:6px; background:var(--cell); color:var(--fg); cursor:pointer; }}
  button:hover {{ border-color:var(--active); }}
  .grid-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:6px; }}
  table {{ border-collapse:collapse; font-variant-numeric:tabular-nums; }}
  th, td {{ border:1px solid var(--line); padding:3px 7px; text-align:right;
            min-width:34px; font-size:12px; }}
  th {{ background:var(--done); font-weight:600; position:sticky; top:0; }}
  td.filled {{ background:var(--done); }}
  td.dep {{ background:var(--dep); color:#111; }}
  td.active {{ background:var(--active); color:#fff; font-weight:700; }}
</style>
</head>
<body>
<h1>{title}</h1>
<pre>{summary}</pre>
<div class="controls">
  <button id="play">Play</button>
  <button id="step">Step</button>
  <button id="reset">Reset</button>
  <input id="speed" type="range" min="1" max="200" value="60">
  <span id="status"></span>
</div>
<div class="grid-wrap"><table id="grid"></table></div>
<script>
const DATA = {payload};
const grid = document.getElementById('grid');
const status = document.getElementById('status');
let cells = [], at = 0, timer = null;

function build() {{
  grid.innerHTML = '';
  const head = grid.insertRow();
  head.appendChild(document.createElement('th'));
  for (const label of DATA.colLabels) {{
    const th = document.createElement('th');
    th.textContent = label;
    head.appendChild(th);
  }}
  cells = [];
  for (let r = 0; r < DATA.rows; r++) {{
    const row = grid.insertRow();
    const th = document.createElement('th');
    th.textContent = DATA.rowLabels[r];
    row.appendChild(th);
    const line = [];
    for (let c = 0; c < DATA.cols; c++) {{
      const td = row.insertCell();
      td.textContent = '';
      line.push(td);
    }}
    cells.push(line);
  }}
}}

function apply(i) {{
  for (const row of cells) for (const td of row) td.classList.remove('active', 'dep');
  const s = DATA.steps[i];
  const td = cells[s.r][s.c];
  td.textContent = s.v;
  td.classList.add('filled', 'active');
  for (const [dr, dc] of s.d) cells[dr][dc].classList.add('dep');
  status.textContent = `step ${{i + 1}} / ${{DATA.steps.length}}` +
    (DATA.truncated ? ' (truncated)' : '');
}}

function step() {{
  if (at >= DATA.steps.length) {{ stop(); return; }}
  apply(at++);
}}
function stop() {{ clearInterval(timer); timer = null;
  document.getElementById('play').textContent = 'Play'; }}
document.getElementById('step').onclick = () => {{ stop(); step(); }};
document.getElementById('play').onclick = () => {{
  if (timer) {{ stop(); return; }}
  document.getElementById('play').textContent = 'Pause';
  timer = setInterval(step, 201 - document.getElementById('speed').value);
}};
document.getElementById('reset').onclick = () => {{ stop(); at = 0; build();
  status.textContent = ''; }};
document.getElementById('speed').oninput = () => {{
  if (timer) {{ clearInterval(timer);
    timer = setInterval(step, 201 - document.getElementById('speed').value); }}
}};
build();
</script>
</body>
</html>
"""


if __name__ == "__main__":  # pragma: no cover - demonstration entry point
    import math
    import os
    import time

    print("=== Edit distance: 'kitten' -> 'sitting' ===")
    problem = edit_distance("kitten", "sitting")
    solution = problem.solve((6, 7))
    print(f"distance = {solution.value((6, 7))}")
    print(analyze(solution).summary())

    print("\n=== 0/1 knapsack, 40 items, capacity 200 ===")
    import random

    rng = random.Random(3)
    weights = [rng.randrange(1, 40) for _ in range(40)]
    values = [rng.randrange(1, 100) for _ in range(40)]
    problem = knapsack(weights, values, 200)
    solution = problem.solve((40, 200))
    print(f"best value = {solution.value((40, 200))}")
    print(analyze(solution).summary())

    print("\n=== Detecting an asymptotic speedup ===")
    counts = [rng.randrange(1, 50) for _ in range(260)]
    prefix = [0]
    for value in counts:
        prefix.append(prefix[-1] + value)

    def merge_cost(i: int, j: int) -> float:
        """Cost of merging files i..j-1: the classic optimal-merge DP."""
        return float(prefix[j] - prefix[i])

    small = 12
    holds = satisfies_quadrangle_inequality(merge_cost, small)
    print(f"quadrangle inequality holds: {holds}")

    n = 260
    t0 = time.perf_counter()
    slow = naive_interval_dp(n, merge_cost)
    t_slow = time.perf_counter() - t0
    t0 = time.perf_counter()
    fast = knuth_interval_dp(n, merge_cost)
    t_fast = time.perf_counter() - t0
    assert math.isclose(slow, fast), (slow, fast)
    print(f"  interval DP over {n} positions:")
    print(f"    naive O(n^3)  {t_slow * 1e3:8.1f}ms -> {slow:.0f}")
    print(
        f"    Knuth O(n^2)  {t_fast * 1e3:8.1f}ms -> {fast:.0f}  ({t_slow / t_fast:.0f}x)"
    )

    # The layered shape: partition sorted points into `groups` clusters,
    # minimising the total squared span. dp[g][i] depends only on dp[g-1][*].
    size, groups = 1_500, 8
    points = sorted(rng.random() * 1000 for _ in range(size))

    def cluster_cost(j: int, i: int) -> float:
        """Squared span of points j..i-1. Convex, so the argmin is monotone."""
        if j >= i:
            return 0.0
        span = points[i - 1] - points[j]
        return span * span

    layer0 = [0.0] + [float("inf")] * size

    t0 = time.perf_counter()
    layer = layer0
    for _ in range(groups):
        layer = [
            min(
                (layer[j] + cluster_cost(j, i) for j in range(i + 1)),
                default=float("inf"),
            )
            for i in range(size + 1)
        ]
    t_quadratic = time.perf_counter() - t0
    naive_answer = layer[size]

    t0 = time.perf_counter()
    layer = layer0
    for _ in range(groups):
        layer = divide_and_conquer_dp(layer, cluster_cost)
    t_dc = time.perf_counter() - t0
    assert math.isclose(naive_answer, layer[size], rel_tol=1e-9), (
        naive_answer,
        layer[size],
    )
    print(f"  layered DP, {size} positions x {groups} layers:")
    print(f"    naive O(k n^2)      {t_quadratic * 1e3:8.1f}ms -> {naive_answer:.1f}")
    print(
        f"    D&C   O(k n log n)  {t_dc * 1e3:8.1f}ms -> {layer[size]:.1f}"
        f"  ({t_quadratic / t_dc:.0f}x)"
    )

    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_trace.html")
    problem = edit_distance("kitten", "sitting")
    render_html(problem.solve((6, 7)), output, title="Edit distance: kitten to sitting")
    print(f"\nWrote animated trace to {output}")
