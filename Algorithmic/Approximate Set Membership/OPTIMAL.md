# Optimal Solution: Approximate Set Membership

**Challenge:** store a set `S` of `n` keys so that membership queries are answered
with no false negatives and at most an `ε` chance of a false positive, using as
little memory as possible.

**Short answer:** a Bloom filter is _not_ the optimal solution and has not been
for over a decade. For a static set, a **homogeneous ribbon filter** stores the
set in about `1.02 × log₂(1/ε)` bits per key — within 2% of the proven lower
bound — versus a Bloom filter's `1.44 ×`. For a set that changes, a **cuckoo
filter** is the best practical option. Implementation:
[`optimal_filters.py`](optimal_filters.py).

---

## 1. The lower bound, which fixes what "optimal" means

Carter, Floyd, Gill, Markowsky and Wegman (1978) proved that any structure
answering membership for an `n`-element subset of a large universe with
one-sided error `ε` needs at least

$$n \log_2 \frac{1}{\varepsilon} \text{ bits.}$$

The argument is a counting one: the structure partitions the universe into an
"accept" set and a "reject" set; the accept set must contain all of `S` and at
most an `ε` fraction of everything else, and there are enough distinguishable
such partitions to force that many bits.

This bound is the yardstick. At `ε = 2⁻⁸` it says **8 bits per key**. Everything
below is scored as a multiple of it.

| Structure                              | Bits/key at `ε = 2⁻⁸` |  Overhead | Deletes | Probes per query |
| :------------------------------------- | --------------------: | --------: | :------ | :--------------- |
| **Lower bound**                        |              **8.00** | **1.00×** | —       | —                |
| Homogeneous ribbon (`w=256`, slack 2%) |              **8.17** | **1.02×** | no      | 1 window         |
| BuRR (bumped ribbon, published)        |                 ~8.04 |   ~1.005× | no      | 1–2 windows      |
| Binary fuse, 8-bit                     |                  9.34 |     1.17× | no      | 3 adjacent       |
| Xor filter, 8-bit                      |                  9.84 |     1.23× | no      | 3 scattered      |
| Classic Bloom                          |                  11.5 |     1.44× | no      | 8 scattered      |
| Cuckoo filter, 12-bit                  |                  15.7 |     1.68× | **yes** | 2 buckets        |
| Blocked Bloom                          |                  15.0 |     1.56× | no      | **1 cache line** |

The measured columns come from running `python optimal_filters.py` over 200 000
keys; they are not quoted from the papers.

---

## 2. The optimal solution: homogeneous ribbon filter

Dillinger, Hübschle-Schneider, Sanders and Walzer (SEA 2022, best paper; JACM
2025). This is the structure to reach for when memory is the binding constraint.

### The construction

Give each key `x` a start offset `s(x)` uniform in `[0, m−w]` and a random
`w`-bit coefficient row `c(x)` with bit 0 forced on. Look for a table `Z` of `m`
words of `r` bits satisfying the **homogeneous** GF(2) system

$$\bigoplus_{j \,:\, c(x)_j = 1} Z[s(x)+j] \;=\; 0 \qquad \text{for every } x \in S.$$

A query recomputes that XOR and reports membership iff the result is zero.

### Why this is the right structure

Three properties fall out at once, and no other filter has all three:

1. **It cannot fail to build.** A homogeneous system is always consistent —
   `Z = 0` solves it. Xor and fuse filters solve an _inhomogeneous_ system by
   peeling, which fails with some probability and needs seed retries; ribbon
   construction has no failure branch at all.
2. **The overhead is only the slack.** The table is `m` words with `m` barely
   above `n`. There is no separate "fingerprint" budget and no load-factor
   ceiling — the space overhead _is_ `m/n − 1`.
3. **Everything is local.** A key's non-zero coefficients live in a window of
   `w` consecutive slots. Gaussian elimination stays inside the band, so
   construction is `O(n · w / 64)` word operations and a query touches one
   contiguous span.

The one trap: **the free variables must be filled randomly.** Leaving them zero
yields `Z = 0`, which satisfies every equation and therefore accepts every
query. This is the kind of bug that passes a "no false negatives" test suite
perfectly while making the filter useless.

### An empirical finding worth stating plainly

The false positive rate is **not** `2⁻ʳ`, and the parameter that controls the
gap is not documented as sharply as it deserves to be. A query is a _guaranteed_
false positive whenever its coefficient row lies in the span of the key rows
overlapping its window. A window of `w` slots is overlapped by roughly
`w/(1+slack)` key rows, leaving about `slack × w` free dimensions — so the
excess error decays in **the product `slack × w`**, not in either parameter
alone.

Measured over 40 000 keys at `r = 8` (reproduce with the sweep in
`test_ribbon_error_collapses_once_slack_times_width_clears_the_cliff`):

| slack | `w` | `slack × w` | bits/key | measured fpp ÷ 2⁻⁸ |
| ----: | --: | ----------: | -------: | -----------------: |
|  0.02 |  64 |         1.3 |     8.17 |  **33.2** ← broken |
|  0.02 | 128 |         2.6 |     8.19 |               1.01 |
|  0.02 | 256 |         5.1 |     8.21 |               0.96 |
|  0.05 |  64 |         3.2 |     8.41 |         3.99 ← bad |
|  0.05 | 128 |         6.4 |     8.43 |               0.96 |
|  0.10 |  64 |         6.4 |     8.81 |               0.90 |
|  0.20 |  64 |        12.8 |     9.61 |               0.95 |

The cliff is sharp and sits near `slack × w ≈ 2.5`.

**The practical consequence — spend slack on width, not on slots.** Look at the
first three rows: tripling `slack × w` from 1.3 to 5.1 fixes a 33× error blowup
at a cost of **0.04 bits per key** (0.5%). Getting the same product by raising
slack instead would cost 1.4 bits per key (17%). Widening the ribbon is nearly
free in memory and costs only construction time; adding slots costs memory
linearly. `recommended_width()` encodes this, targeting `slack × w ≥ 5`.

This is why the default configuration is `slack = 0.02, w = 256` rather than the
`slack = 0.05, w = 64` that a first reading of the paper suggests.

### A Python-specific implementation note

The query needs the XOR of up to `w` bytes selected by a bit mask. A per-bit
Python loop costs `w` interpreted iterations. Instead the implementation reads
the whole `w`-byte window as one big integer, expands the coefficient row into a
byte mask through a 256-entry table, ANDs, and XOR-folds with `log₂(w)+3`
shift-XOR steps. Every step runs in CPython's C big-integer code, turning a
256-iteration Python loop into about 20 C-level operations. The same routine
does back-substitution during construction.

---

## 3. Runner-up: binary fuse filter

Graf and Lemire (ACM JEA 2022). At 9.34 bits/key it gives up 14% of the ribbon's
space advantage, and in exchange the query is three plain array reads with no
mask arithmetic — in a compiled language it is the fastest of the space-efficient
filters, and it is much simpler to get right.

Each key maps to three slots and an 8-bit fingerprint `f(x)`, with the array
built so that `F[h₀] ^ F[h₁] ^ F[h₂] = f(x)`. Construction is by **peeling**:
repeatedly find a slot touched by exactly one remaining key, record it, remove
that key; then assign values in reverse peeling order, so each key gets a slot
no later assignment disturbs.

The "fuse" geometry is the contribution: `h₀` lands in segment `s`, `h₁` in
`s+1`, `h₂` in `s+2`. Confining the probes to a narrow window improves locality
_and_, less obviously, lowers the peeling threshold — which is where the space
saving over the xor filter (9.84 → 9.0 bits/key) comes from.

**Failure mode worth knowing:** duplicate keys hash to identical slot triples
under _every_ seed, so peeling can never succeed and the retry loop is
guaranteed to exhaust. The implementation raises `FuseConstructionError` naming
duplicates as the likely cause rather than looping.

---

## 4. When the set changes: cuckoo filter

Fan, Andersen, Kaminsky and Mitzenmacher (CoNEXT 2014). Ribbon and fuse filters
solve a global system and are strictly static. When keys must be _deleted_, the
cuckoo filter is the answer; it beats a counting Bloom filter on space for any
`ε` below roughly 3%.

The trick that makes it work without storing keys is **partial-key cuckoo
hashing**: the alternate bucket is `i₂ = i₁ ⊕ hash(f)`, derived from the
fingerprint alone, so a displaced fingerprint can be relocated without knowing
which key produced it. This forces the bucket count to be a power of two — the
XOR is only an involution modulo `2^k`.

Two correctness traps, both handled in the implementation:

- **The dropped victim.** When the eviction chain gives up it is still _holding_
  a fingerprint that has already been removed from its bucket. Dropping it
  silently loses a key that was legitimately inserted earlier — a false
  negative, which is supposed to be impossible. A one-slot victim cache fixes
  it. This bug is easy to write and hard to notice: it only manifests near
  saturation.
- **Unsound deletion.** Deleting a key that was never inserted can remove a
  colliding fingerprint belonging to a real key. This is inherent to the
  structure, not to the implementation, and callers must respect it.

---

## 5. When throughput is the constraint: blocked Bloom

A classic Bloom filter's `k` probes are `k` independent cache misses. A blocked
Bloom filter picks _one_ 512-bit block — one cache line — and sets all `k` bits
inside it, so a query costs a single miss. Measured at 15.0 bits/key it is the
worst structure here on space (confining bits to one block makes the per-block
load uneven, which costs 20–30%), and the best on throughput. It is the right
answer only when the filter does not fit in cache and queries dominate.

---

## 6. Non-optimal alternatives, and why each loses

| Alternative                                            | Why it is not optimal                                                                                                                                                                                                         |
| :----------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Classic Bloom filter**                               | `1.44×` the bound, and the 44% is structural: it comes from the bits being set independently rather than solving a system. No amount of tuning `k` and `m` removes it. Also `k` scattered cache misses per query.             |
| **Counting Bloom filter**                              | Supports deletes but multiplies space by 3–4× (a counter per bit instead of a bit). A cuckoo filter dominates it for any `ε` below ~3%.                                                                                       |
| **Xor filter** (Graf & Lemire 2020)                    | 9.84 bits/key and three _scattered_ probes. Binary fuse strictly supersedes it — same idea, better geometry, less space, faster construction. Included only for historical context.                                           |
| **Golomb-coded sequence / compressed static function** | Reaches the entropy bound in space, but queries require decoding a variable-length stream — orders of magnitude slower. Right for archival, wrong for a filter.                                                               |
| **Perfect hash + fingerprint array**                   | Genuinely reaches ~`log₂(1/ε) + 1.5` bits/key and is a real contender. Loses to ribbon on construction time and on the extra indirection through the MPHF. Worth considering if an MPHF is already present for other reasons. |
| **Quotient filter**                                    | Cache-friendly and supports deletes and resizing, but pays ~`2.125×` for metadata bits, worse than cuckoo at comparable `ε`. Its real advantage is mergeability, which the others lack.                                       |
| **Sorted array + binary search**                       | Exact, no false positives, but `Θ(n log u)` bits — it stores the keys. Different problem.                                                                                                                                     |
| **Hash set**                                           | Same; exact and much larger. If the set fits in memory exactly, no filter is needed.                                                                                                                                          |

### Not implemented, and why

**BuRR** (Bumped Ribbon Retrieval, same authors, SEA 2022 best paper) is the
true state of the art at ~1.005× the bound. It splits the table into small
chunks and "bumps" the keys that fail to fit into a fallback layer, which
removes the slack the plain ribbon filter needs. The remaining gap to the
implementation here is **0.13 bits per key (1.6%)**, in exchange for a
multi-layer structure with a recursive fallback and a per-chunk metadata
encoding. That trade did not seem worth it for a reference implementation; the
plain homogeneous ribbon captures essentially all of the available win at a
fraction of the complexity. This is a deliberate stopping point, not an
oversight.

---

## 7. Choosing

```
Does the set change after construction?
├── Yes, with deletions ─────────────► CuckooFilter
├── Yes, insert-only, unknown size ──► BlockedBloomFilter (or classic Bloom)
└── No (static, all keys known)
    ├── Memory is the constraint ────► HomogeneousRibbonFilter   ← 1.02× optimal
    ├── Query throughput dominates ──► BinaryFuse8Filter
    └── Filter exceeds cache size ───► BlockedBloomFilter
```

## 8. A caveat that applies to all of them

Every filter here uses a non-cryptographic hash. An adversary who can choose
inputs and observe outcomes can find keys that collide and drive the false
positive rate to 1. If inputs are attacker-controlled — a network service, a
public API — substitute a keyed hash (SipHash-1-3, or `siphash` from
`hashlib.blake2b` with a secret key) for `hash_bytes`, and keep the key secret.
The structural analysis above is unchanged; only the hash needs replacing.

---

## References

- Carter, Floyd, Gill, Markowsky, Wegman, _Exact and approximate membership testers_, STOC 1978. (The lower bound.)
- Bloom, _Space/time trade-offs in hash coding with allowable errors_, CACM 1970.
- Fan, Andersen, Kaminsky, Mitzenmacher, _Cuckoo Filter: Practically Better Than Bloom_, CoNEXT 2014.
- Graf, Lemire, _Xor Filters: Faster and Smaller Than Bloom and Cuckoo Filters_, ACM JEA 2020.
- Graf, Lemire, [_Binary Fuse Filters: Fast and Smaller Than Xor Filters_](https://arxiv.org/abs/2201.01174), ACM JEA 2022.
- Dillinger, Hübschle-Schneider, Sanders, Walzer, [_Fast Succinct Retrieval and Approximate Membership Using Ribbon_](https://arxiv.org/abs/2109.01892), SEA 2022 (best paper); journal version [_Ribbon: Fast Succinct Static Retrieval and Approximate Membership_](https://dl.acm.org/doi/10.1145/3785417), JACM 2025.
- [BuRR reference implementation](https://github.com/lorenzhs/BuRR).
