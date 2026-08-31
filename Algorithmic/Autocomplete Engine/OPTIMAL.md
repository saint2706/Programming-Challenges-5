# Optimal Solution: Autocomplete Engine

**Challenge:** given a dictionary of scored terms, return the `k` highest-scoring
terms starting with a query prefix.

**Short answer:** the trie is the easy half and the wrong thing to optimise. A
plain trie finds the prefix in `O(p)` and then enumerates and sorts the *entire*
subtree — so answering "top 10 for `a`" over a million terms touches a hundred
thousand nodes. Augment every node with the best completion in its subtree and a
best-first traversal returns the same answer in **`O(p + k log k)`**, touching
`O(k)` nodes. Measured: **200–470× faster**. Implementation:
[`optimal_autocomplete.py`](optimal_autocomplete.py).

---

## 1. What the naive solution actually costs

The standard advice — "use a trie, prefix lookup is `O(p)`" — is true and
misleading. Prefix *lookup* is `O(p)`; prefix *ranking* is not:

| Step | Cost |
| :-- | :-- |
| Descend to the prefix node | `O(p)` |
| Enumerate the subtree | `O(N_p)` nodes, where `N_p` = terms sharing the prefix |
| Sort by score | `O(N_p log N_p)` |
| Return the first `k` | `O(k)` |

The dominant term is `N_p`, and `N_p` is largest exactly when the user has typed
least — the first keystroke, the one where latency matters most. This is
backwards: **the cost should scale with `k`, the number of results shown, not
with `N_p`, the number of results discarded.**

The current `trie.py` in this directory has this shape; its README states
top-k as `O(L + N log N)`. That is the honest complexity, and it is what the
structures below eliminate.

## 2. The optimal solution: a trie that is also a heap

The insight from Hsu & Ottaviano (WWW 2013): store in **every node the best
completion in its subtree**. The trie becomes simultaneously a prefix index and
a tournament tree over scores.

A query then runs a best-first search from the prefix locus. A priority queue
holds two kinds of entry — "emit this term" and "expand this node" — ordered by
rank key. Repeatedly pop the minimum:

- **Expand entry:** replace the node with its own term (if terminal) and each of
  its children, each keyed by *their* best.
- **Emit entry:** it is the next result.

**Why this is correct.** A node's key is the minimum of its own term's key and
its children's keys. Replacing a popped node by exactly those parts therefore
leaves the queue's minimum unchanged whenever that node held the best remaining
completion. That is precisely the greedy invariant best-first search needs, so
the emitted sequence is globally sorted by score.

Crucially the traversal never enters a subtree whose best is worse than the
`k`-th result already found. The rest of the dictionary is not examined at all.

### Details that matter

**Path compression is not cosmetic.** Without it, a 10-character prefix costs 10
node visits before the locus, and every emitted completion costs one heap
operation per *character* rather than per *branch point*. With compressed edges,
`k` results cost `O(k)` heap operations in the typical case.

**Rank key = `(-score, word)`.** Negating the score lets one plain tuple
comparison and one plain min-heap implement "score descending, then
lexicographic" with no custom comparators, and makes tie-breaking deterministic
— which is what lets the tests compare against a brute-force oracle for exact
equality.

**Recompute the augmentation bottom-up, not top-down.** It is tempting to fold a
running `min` downward as you insert. That is correct for *raising* a score and
silently wrong for *lowering* one: the stale best survives in the ancestors and
keeps ranking a term that no longer deserves the position. Walking back up the
insertion path and recomputing costs the same `O(p)` and handles both.
`test_trie_handles_a_score_being_lowered` pins this.

**Prefixes ending mid-edge.** With compression, `"appl"` may end partway along
the edge leading to `apple`/`application`. The locus is then the node at the
*far* end of that edge, since everything below it still shares the prefix.
Getting this wrong silently returns nothing for exactly the queries users type.

## 3. The static alternative: prefix range + RMQ

If the dictionary never changes, there is a structure with no per-character
nodes at all.

Sort the terms lexicographically. Then **all terms with a given prefix form a
contiguous range**, found with two binary searches. Top-k completion becomes:
report the `k` largest values in an array range.

That problem has a clean recursive answer. The maximum of the range is the first
result; it splits the range in two, and the next result is the better of those
halves' maxima. Keeping candidate subranges in a priority queue emits results in
order at one range-maximum query each.

```
lo, hi = prefix_range(prefix)
heap = { (max of [lo,hi), lo, hi) }
repeat k times:
    pop the best range, emit its maximum at index m
    push [lo, m) and [m+1, hi)
```

Storage is two flat arrays plus a segment tree of `2n` integers — dramatically
less than a node object per character. In the benchmark it builds **11× faster**
than the trie and queries about **2× faster**. The cost is that it is completely
static.

**Segment tree vs. sparse table.** A sparse table answers range-max in `O(1)`
instead of `O(log n)`, but needs `O(n log n)` memory. Since the heap already
costs `log k` per result, the segment tree's extra `log n` is rarely the
bottleneck, and `2n` integers is the better default. Swap it in if profiling
says otherwise.

**Two subtleties.** The upper end of a prefix range needs the smallest string
sorting after every string with that prefix — increment the last character, and
if it is already the maximum code point, strip it and retry; if the prefix is
entirely maximum code points, the range runs to the end of the dictionary.
Separately, the segment tree stores *indices* and breaks ties leftward, which,
because the terms are sorted, makes ties break lexicographically for free —
matching the trie exactly.

## 4. Measured results

200 000 random terms over an 8-letter alphabet, CPython 3.11, `k = 10`:

| Prefix | Terms matching | Filter + sort | CompletionTrie | RmqIndex | Speedup |
| :-- | --: | --: | --: | --: | --: |
| `a` | 25 100 | 51.20 ms | **0.164 ms** | 0.069 ms | **312×** |
| `ab` | 3 095 | 22.55 ms | 0.117 ms | 0.061 ms | 193× |
| `abc` | 383 | 19.11 ms | 0.090 ms | 0.047 ms | 212× |
| `abcd` | 52 | 18.70 ms | 0.040 ms | 0.031 ms | 466× |

Build: trie 5.51 s, RMQ index 0.48 s.

The shape of the trie column is the result. Going from 52 matching terms to
25 100 — a 480× increase — costs 4× more query time, not 480×. The remaining
growth is the deeper heap, not subtree enumeration.

## 5. Non-optimal alternatives, and why each loses

| Alternative | Verdict |
| :-- | :-- |
| **Plain trie + enumerate + sort** | The baseline. `O(p + N_p log N_p)`; cost peaks on the first keystroke. What everything here exists to replace. |
| **Trie + per-node cached top-k list** | Genuinely `O(p + k)` queries — faster than best-first. But it stores `k` entries per node (so `k` must be fixed at build time), and an update touches every ancestor's cached list. Right for a frozen index with a known `k`; wrong as a general structure. Hsu & Ottaviano's "Completion Trie" is the refined version, which may still visit `Ω(k·l)` nodes. |
| **Hash map from every prefix to its top-k** | `O(1)` queries and quadratic space: a term of length `l` appears under `l` prefixes. Viable only for short terms or a capped prefix length, which is a real production tactic but not a general solution. |
| **Ternary search tree** | Better constant factors than a 26-way trie and less memory, but the ranking problem is *identical* — it optimises the half that was never the bottleneck. |
| **DAWG / MA-FSA** | Excellent compression by merging equivalent suffixes. Incompatible with per-node score augmentation, because merged nodes are shared between terms with different scores. Choose compression or ranking, not both. |
| **FST with weights** (Lucene, `fst` crate) | The production answer in a search engine: near-succinct, and weights along transitions do support ranked traversal. Substantially more machinery — minimisation, output pushing — and effectively static. The right choice at Lucene's scale, over-engineered below it. |
| **Succinct trie (LOUDS) + score-decomposed encoding** | The most space-efficient known approach: Hsu & Ottaviano report sizes competitive with `gzip`, and after locating the locus only `k−1` nodes need visiting. Rank/select structures make it slow in pure Python and much more code. Documented as the frontier, not implemented. |
| **Sorted array + linear scan of the prefix range** | Simple and correct, `O(log n + N_p)`. Strictly dominated by the RMQ index, which shares the array and the binary search and replaces the scan with `k` range-max queries. |
| **Full-text search engine (Elasticsearch, etc.)** | Correct and enormous. Justified when the requirement is really fuzzy matching, multi-field ranking, and analysers; not for prefix completion over a word list. |

### Deliberately not implemented

**Fuzzy / typo-tolerant completion.** Real autocomplete tolerates typos, which
means intersecting a Levenshtein automaton with the trie rather than descending
a literal prefix. That is a genuinely different algorithm and it is the subject
of challenge 4 in this repository — see
[`Approximate String Matching/OPTIMAL.md`](../Approximate%20String%20Matching/OPTIMAL.md).
The two compose: run the automaton intersection to find candidate loci, then use
the augmentation here to rank within them.

## 6. Choosing

```
Does the dictionary change at query time?
├── Yes ─────────────────► CompletionTrie      (O(p + k log k), supports updates)
└── No
    ├── k fixed, memory ample ──► trie + cached top-k lists  (O(p + k))
    ├── memory constrained ─────► RmqCompletionIndex          (2n ints, no nodes)
    └── multi-GB, production ───► weighted FST (Lucene)
```

## 7. Complexity summary

| Operation | `CompletionTrie` | `RmqCompletionIndex` | Plain trie |
| :-- | :-- | :-- | :-- |
| Build | `O(total chars)` | `O(n log n)` | `O(total chars)` |
| `top_k(prefix, k)` | `O(p + k·b·log(k·b))` | `O(log n + k log k log n)` | `O(p + N_p log N_p)` |
| Insert / re-score | `O(p)` | not supported | `O(p)` |
| Space | node per branch point | `2n` ints + terms | node per branch point |

---

## References

- Hsu & Ottaviano, [*Space-efficient data structures for top-k completion*](http://groups.di.unipi.it/~ottavian/files/topk_completion_www13.pdf), WWW 2013. (Completion Trie, RMQ Trie, Score-Decomposed Trie.)
- Bast & Weber, *Type less, find more: fast autocompletion search with a succinct index*, SIGIR 2006.
- Morrison, *PATRICIA — Practical Algorithm To Retrieve Information Coded In Alphanumeric*, JACM 1968. (Path compression.)
- Fischer & Heun, *Space-efficient preprocessing schemes for range minimum queries*, SIAM J. Comput. 2011. (Making the RMQ side succinct.)
