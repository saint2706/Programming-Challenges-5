# Optimal Solution: Approximate String Matching

**Challenge:** compare strings allowing for typos — measure how different two
strings are, find a pattern approximately inside a text, and find a query's
near-matches in a dictionary.

**Short answer:** these are three different problems with three different
optimal answers, and conflating them is the main mistake. Distance: **Myers'
bit-parallel algorithm** (measured **217× faster** than the DP). Substring
search: the same algorithm with one bit changed. Dictionary lookup: a
**Levenshtein automaton over a trie** for large `k`, or **symmetric-delete
indexing** for `k ≤ 2` (measured **76–120×** faster). Implementation:
[`optimal_matching.py`](optimal_matching.py).

---

## 1. Distance: the DP is not optimal, and cannot be improved much

### The lower bound comes first

Backurs & Indyk (STOC 2015) proved that edit distance **cannot** be computed in
`O(n^(2−δ))` time for any `δ > 0` unless the Strong Exponential Time Hypothesis
fails. So the quadratic DP is asymptotically optimal, and there is no clever
subquadratic algorithm waiting to be found.

That sounds like the end of the story. It is not, because it is a statement about
_asymptotics_, and the entire practical win here lives in the constant.

### Myers' bit-vector algorithm

The observation (Myers, JACM 1999): in a Levenshtein DP, **adjacent cells in a
column differ by exactly −1, 0 or +1**. So a column of `m` integers can be
stored as two `m`-bit masks — `vp` marking the +1 positions, `vn` the −1
positions — and advanced by one text character with a fixed sequence of
and/or/add/shift operations.

The elegant part is that a **single integer addition** does the work of the DP's
inner `min` chain: its carry propagation resolves the whole column at once.

`O(n · ⌈m/w⌉)` instead of `O(nm)`. It does not beat the SETH bound; it extracts
the `w`-fold constant that the bound says nothing about.

### Why this fits Python unusually well

In C, Myers' algorithm is limited to `w = 64` bits per word, and patterns longer
than 64 characters need a blocked multi-word implementation with carry plumbing
between blocks — a substantial complication that most implementations skip.

**Python's integers are arbitrary-precision.** The "word" is as wide as the
pattern, so the algorithm stays a single flat loop over the text at any pattern
length, with the bit arithmetic running in CPython's C big-integer code. A
320-character pattern works with no special handling; the test suite pins this.

This is one of the rare cases where Python's number model is a genuine
algorithmic advantage rather than a tax.

**Measured:** two random 2000-character strings — 4.9 ms bit-parallel vs
1025 ms for the two-row DP. **217× faster**, exact same answer.

### What bit-parallelism cannot do

Bit-packing works _because_ adjacent cells differ by at most one. **Weighted
edits break that invariant**, and there is no known bit-parallel algorithm for
the general weighted case. So `levenshtein_dp` stays as the escape hatch for
custom costs — and it is genuinely needed, not vestigial.

One subtlety it exposes: with unequal costs, edit distance is **not symmetric**.
Turning `abc` into `abcd` costs one insertion; the reverse costs one deletion.
The implementation is explicit about direction, and the tests pin the asymmetry.
(The first version of this module had insert and delete transposed throughout —
invisible under unit costs, wrong under any others.)

## 2. Substring search: one bit of difference

Approximate substring search is the _same_ bit-parallel machinery with **one
changed boundary condition**.

- **Whole-string distance:** row 0 of the DP grows `0, 1, 2, …`, because the
  text prefix consumed so far must be paid for. In bit terms: set the low bit
  when shifting the horizontal deltas (`ph = (ph << 1) | 1`).
- **Substring search:** a match may begin anywhere, so row 0 is all zeros. In
  bit terms: don't set that bit (`ph = ph << 1`).

That single bit is the entire difference between "how different are these
strings" and "where does this pattern appear". The practical consequence is
worth stating: approximate grep costs **one distance computation over the whole
text**, not one per starting position, and the cost is independent of `k`.

Measured: a 30-character pattern in 2 000 000 characters at `k ≤ 3` in 1.3 s of
pure Python.

## 3. Dictionary lookup: where the real choice is

Neither algorithm above helps here — running `levenshtein` against all `N` terms
is `O(N)` distance computations. Two structures do better, and **which one wins
depends sharply on `k`**.

### Levenshtein automaton over a trie

Computing distance from a query to every term recomputes the same DP prefix over
and over: `apple`, `apply` and `application` share four characters and therefore
four DP rows. A trie stores each distinct prefix once, so a depth-first walk
computes each shared row **once**, carrying it down as it descends.

The prune is the payoff: a node's row gives the distance from the query to that
node's prefix, and distance only grows as the prefix grows. If every entry of a
node's row already exceeds `k`, no descendant can come back under it — the whole
subtree is skipped unvisited.

### Symmetric-delete indexing (SymSpell)

If two words are within `k` edits, then deleting at most `k` characters from
each can produce a **common** string. So index every word under all of its
delete-variants, and look a query up by its own delete-variants. Candidate
generation involves **no distance computation at all** — pure hash lookup — and
survivors are then verified exactly.

## 4. Measured results, and the finding that changed the recommendation

50 000 random 4–11 character words over a 26-letter alphabet, CPython 3.11:

| `k` | Linear scan | Trie automaton | SymSpell |     Trie speedup | SymSpell speedup |
| --: | ----------: | -------------: | -------: | ---------------: | ---------------: |
|   1 |      119 ms |         8.1 ms |  1.57 ms |        **14.7×** |          **76×** |
|   2 |      162 ms |          80 ms |  1.88 ms |             2.0× |          **87×** |
|   3 |      211 ms |         231 ms |  1.75 ms | **0.9× (worse)** |         **120×** |

**The trie automaton's advantage collapses as `k` grows, and at `k = 3` it is
slower than a linear scan.** This is not an implementation artefact. Every trie
node within `k` levels of the root has a row minimum of at most `k`, so it can
never be pruned: at `k = 3` over a 26-letter alphabet that is `26 + 26² + 26³ ≈
18 000` nodes explored before pruning can begin to bite. The prune only starts
paying below that depth, and by then the linear scan — which rejects most terms
on a length check alone — has already done its work.

This is worth stating plainly because the standard advice ("use a Levenshtein
automaton over a trie") is presented without this caveat, and the caveat covers
the case people most often want. Two things change the picture:

- **A real dictionary prunes better than random strings.** English word lists
  have heavy prefix sharing and a highly non-uniform first-letter distribution,
  so the shallow levels are far narrower than `26^d`. The measurement above is
  close to the adversarial case.
- **SymSpell is flat in `k`** on the query side — its cost is the number of
  delete-variants of the _query_, not of the dictionary — which is why it wins
  by two orders of magnitude across the board.

**So the honest recommendation inverts the usual one:** for spelling correction
(`k ≤ 2`, the overwhelmingly common case), use symmetric-delete indexing. Reach
for the trie automaton when the index memory is unacceptable, or when `k` is
large enough that SymSpell's combinatorial index is not buildable.

SymSpell's price is that index. At `k = 3` over 50 000 words it holds **4.08
million** entries and takes 15 s to build, against the trie's 0.44 s. It buys
query speed with memory and build time, and the trade is worth it whenever
queries outnumber rebuilds — which for spelling correction they overwhelmingly do.

## 5. Non-optimal alternatives, and why each loses

| Alternative                                        | Verdict                                                                                                                                                                                                                                                                                                                                                                                                                       |
| :------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Full `O(mn)` DP with a full matrix**             | Correct; uses `O(mn)` memory for no benefit when only the distance is wanted. Keep the matrix only when the alignment must be reconstructed.                                                                                                                                                                                                                                                                                  |
| **Two-row DP**                                     | The right _reference_ implementation and the only way to support weighted edits. 217× slower than bit-parallel at unit costs.                                                                                                                                                                                                                                                                                                 |
| **BK-tree** (what the current `README` recommends) | Uses the triangle inequality to prune by distance to arbitrary pivots. Strictly dominated by the trie automaton: same `O(N)` worst case, weaker pruning, _and_ it cannot share prefix work — every candidate needs a full distance computation, whereas the trie computes each shared prefix's row once. Its one advantage is generality: it works in any metric space, not just over strings. Use it for that, not for this. |
| **N-gram / q-gram inverted index**                 | Filters by shared `q`-grams, then verifies. Genuinely useful at scale and the basis of production fuzzy search, but it is a _filter_, not an algorithm: recall depends on the `q`-gram threshold, and short strings have too few grams to filter on. Complementary to, not a replacement for, the above.                                                                                                                      |
| **Ukkonen's banded DP**                            | `O(kn)` by computing only the diagonal band of width `2k+1`. A real improvement over the full DP and the right answer when `k` is small and bit-parallelism is unavailable. Bit-parallel already beats it at any `k` for which both apply, since its cost is independent of `k`.                                                                                                                                              |
| **Landau–Vishkin**                                 | `O(kn)` via suffix-tree LCP jumps — asymptotically excellent, with constants so poor it is essentially never faster in practice. A theory result.                                                                                                                                                                                                                                                                             |
| **Four Russians** (Masek–Paterson)                 | `O(n²/log n)` by precomputing blocks. Superseded in every practical sense by bit-parallelism, which achieves the same `log`-factor win with a fraction of the machinery.                                                                                                                                                                                                                                                      |
| **`difflib.SequenceMatcher`**                      | In the standard library, and computes a _different_ thing — longest contiguous matching blocks, not edit distance. Its `ratio()` is not a metric and violates the triangle inequality. Fine for "how similar do these look"; wrong wherever a distance bound is needed.                                                                                                                                                       |
| **Soundex / Metaphone**                            | Phonetic hashing, not edit distance. Solves "sounds alike", collapses distinctions that matter, and is English-specific. Different problem.                                                                                                                                                                                                                                                                                   |
| **Embedding + vector search**                      | Semantic similarity, not orthographic. Will happily rate `car` and `automobile` as close and `apple` and `aple` as far. Different problem again.                                                                                                                                                                                                                                                                              |

### Deliberately not implemented

**The universal Levenshtein automaton** (Schulz & Mihov 2002). Rather than
running a DP row per trie node, precompute a single automaton — for a fixed `k`,
independent of the query — whose transitions are driven by a small
characteristic vector. This turns the per-node cost from `O(m)` into `O(1)` and
is the genuinely optimal construction. It needs a state-space enumeration and a
transition table per `k`, which is a substantial amount of machinery for a
constant-factor win that, per the measurements above, does not change the
_recommendation_ — SymSpell still wins at the `k` values that matter. Documented
as the frontier.

**Ukkonen banding inside the trie traversal.** Restricting each node's row to
the `2k+1` diagonal band would cut the per-node cost by roughly 2× at typical
word lengths. It does not address the real problem, which is the _number of
nodes visited_, not the cost per node.

## 6. Choosing

```
Comparing two specific strings?
├── Unit costs ─────────────► levenshtein()      (Myers, 217x faster)
└── Weighted edits ─────────► levenshtein_dp()   (no bit-parallel option exists)

Finding a pattern inside a long text?
└──────────────────────────► search()            (one pass, cost independent of k)

Finding near-matches in a dictionary?
├── k <= 2, memory available ► SymSpellIndex     (76-120x; ~80 index entries/word)
├── k >= 3, or memory tight  ► FuzzyDictionary   (prunes; degrades as k grows)
└── millions of terms ───────► q-gram index + verification with bounded_levenshtein
```

## 7. Complexity summary

| Operation                | Time                            | Space          | Notes                        |
| :----------------------- | :------------------------------ | :------------- | :--------------------------- |
| `levenshtein`            | `O(n·⌈m/w⌉)`                    | `O(m)` bits    | Optimal up to SETH           |
| `levenshtein_dp`         | `O(mn)`                         | `O(min(m,n))`  | Weighted edits               |
| `search`                 | `O(n·⌈m/w⌉)`                    | `O(m)` bits    | Independent of `k`           |
| `FuzzyDictionary.search` | `O(V·m)`, `V` = surviving nodes | trie           | `V → all nodes` as `k` grows |
| `SymSpellIndex.search`   | `O(C(m,≤k))` lookups            | `O(N·C(m,≤k))` | Flat in dictionary size      |

---

## References

- Myers, _A fast bit-vector algorithm for approximate string matching based on dynamic programming_, JACM 46(3), 1999.
- Hyyrö, _A bit-vector algorithm for computing Levenshtein and Damerau edit distances_, Nordic Journal of Computing, 2003. (The formulation implemented here.)
- Backurs & Indyk, _Edit distance cannot be computed in strongly subquadratic time (unless SETH is false)_, STOC 2015.
- Ukkonen, _Algorithms for approximate string matching_, Information and Control 64, 1985.
- Schulz & Mihov, _Fast string correction with Levenshtein automata_, IJDAR 5, 2002.
- Masek & Paterson, _A faster algorithm computing string edit distances_, JCSS 20, 1980.
- Garbe, [_SymSpell: 1000× faster spelling correction_](https://github.com/wolfgarbe/SymSpell).
- Navarro, _A guided tour to approximate string matching_, ACM Computing Surveys 33(1), 2001. (The survey that maps the whole field.)
