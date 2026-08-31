# Optimal Solution: Consistent Hashing

**Challenge:** map keys to nodes so that adding or removing a node moves as few
keys as possible.

**Short answer:** the hash ring is what "consistent hashing" usually means, and
it has not been the best answer for about a decade. **AnchorHash** (2019/2021)
achieves all four desirable properties at once — minimal disruption, near-perfect
balance, `O(1)` lookup, and removal of _any_ node — which nothing before it
managed. Implementation: [`optimal_hashing.py`](optimal_hashing.py).

---

## 1. First, define the goal correctly

Four properties are wanted, and the literature is careless about the first one:

1. **Minimal disruption.** Removing a node moves **only that node's keys**, and
   no others.
2. **Balance.** Every node gets close to `1/N` of the keys.
3. **Fast lookup.**
4. **Arbitrary membership change** — any node can leave, not just the last one.

The usual phrasing of (1) is "moves `1/N` of the keys", and that is **not the
same thing**. A node holding less than its share moves fewer than `1/N` keys
while still shuffling other nodes' keys around — it would pass the `1/N` test
while violating the property. The measurement harness here therefore reports
_how many keys moved that did not belong to the departing node_. That number is
zero exactly when the algorithm is minimally disruptive, and it is what
separates Maglev from the rest below.

## 2. Measured comparison

Removing one node from a 20-node cluster, 200 000 keys:

| Algorithm        | peak/mean | Keys moved | Departing node held | Needlessly moved | Verdict         |
| :--------------- | --------: | ---------: | ------------------: | ---------------: | :-------------- |
| HashRing (v=160) | **1.105** |      4.53% |               4.53% |           0.000% | minimal         |
| JumpHash (tail)  |     1.018 |      5.05% |               5.05% |           0.000% | minimal         |
| RendezvousHash   |     1.017 |      5.01% |               5.01% |           0.000% | minimal         |
| MaglevHash       |     1.019 |      5.28% |               4.93% |       **0.349%** | **NOT minimal** |
| **AnchorHash**   | **1.014** |      5.02% |               5.02% |           0.000% | minimal         |

Lookup throughput, 20 nodes, CPython:

| Algorithm        | µs/lookup |
| :--------------- | --------: |
| MaglevHash       |  **2.76** |
| HashRing (v=160) |      2.97 |
| AnchorHash       |      3.13 |
| JumpHash         |      4.33 |
| RendezvousHash   |     67.51 |

Two things stand out. The ring is **the worst-balanced of the five** despite
carrying 3 200 virtual nodes — a 10.5% peak overload against AnchorHash's 1.4%
with no virtual nodes at all. And Maglev's non-minimality is not a rounding
error: 0.349% of keys belonging to _surviving_ nodes were reshuffled, which for
a stateful system means moving real data for no reason.

## 3. The optimal solution: AnchorHash

Mendelson, Vargaftik, Barabash, Hay, Keslassy, Orda (IEEE/ACM ToN 2021).

**The idea.** Fix an _anchor_ set of `a` bucket slots up front — the largest the
cluster will ever be. A key hashes uniformly into the anchor. If it lands on a
working bucket, done. If it lands on a _removed_ bucket `b`, the algorithm
**replays history**: it re-hashes the key into the working set as it existed at
the moment `b` was removed, and repeats until it reaches a working bucket.

The trick that makes this possible is that `A[b]` stores the _size_ of the
working set when `b` was removed. That single number identifies the historical
set well enough to re-hash into it, without storing the set.

**Why removal is minimal.** Keys that never landed on `b` are untouched by
definition — their path through the anchor does not mention `b`. Keys that did
land on `b` get redistributed over exactly the set that existed when `b` left.
No surviving node loses anything.

**Why it is fast.** The expected number of replay steps is `O(ln(a/N))`, so
keeping the anchor within a small factor of the working set makes lookups
effectively constant time. The bookkeeping is three integer arrays of size `a`:

- `A[b]` — working-set size when `b` was removed; `0` means working.
- `W`/`L` — a swap-with-last working set with its reverse index.
- `K[b]` — the bucket that took `b`'s place when `b` was removed.

All updates are `O(1)`, and — the property tested in
`test_anchor_hash_add_restores_the_previous_assignment` — remove-then-add
returns every key exactly where it started, because the add operation precisely
inverts the swap the removal performed.

## 4. The other three, and what each is actually for

### JumpHash — zero memory, perfect balance, and one fatal restriction

Lamping & Veach (2014) is remarkable for what it does _not_ have: **no data
structure at all**. Twenty lines of arithmetic, `O(ln N)` time, zero bytes of
state, and the best balance in the table.

The idea: going from `n` to `n+1` buckets, a key must move to the new bucket
with probability exactly `1/(n+1)`. Rather than simulating every step, _sample
the jumps_ — draw the next `n` at which a move occurs from the implied geometric
distribution. Only `O(ln N)` jumps happen, so the loop is short.

**The catch is real.** Buckets are the integers `0..N-1`, and the only change
covered is growing or shrinking at the **tail**. Removing bucket 3 from a set of
10 is inexpressible — you can only go to 9 buckets, which renumbers everything.
Perfect for sharding a dataset over a resizable pool; unusable for a load
balancer over named servers that fail individually.

### RendezvousHash — the one that does weights properly

Thaler & Ravishankar (1998). Score every node against the key, take the highest.
Minimal disruption is immediate: removing a node only affects keys whose maximum
it was.

Its distinguishing feature is **native weighting**. Scaling the score by
`−weight / ln(u)`, where `u` is the node's hash mapped into `(0,1)`, makes the
probability of winning _exactly_ proportional to the weight. That is an exact
result, not an approximation — and something the ring can only imitate by handing
bigger nodes more virtual nodes. It also yields a stable replica set for free:
the top `r` nodes degrade minimally too.

The cost is `O(N)` per lookup — 22× slower than everything else in the table at
20 nodes, and worse from there. Fine for tens of nodes, wrong for thousands.

### MaglevHash — deliberately not minimal, and shipped anyway

Eisenbud et al. (Google, NSDI 2016). Precompute a table of `M` entries (`M`
prime); a lookup is one array index — the fastest in the table. Each node
proposes a permutation of table positions from an offset and a co-prime skip,
and nodes take turns claiming their most-preferred unclaimed slot.

It **is not minimally disruptive**, as measured above, and this is worth
understanding rather than filing as a defect. A Maglev load balancer fronts
connection-tracked flows: existing connections are pinned by the connection
table, so a remap only affects _new_ ones. Disruption is nearly free in that
setting; `O(1)` lookup at line rate is not. Google optimised the thing that was
scarce.

The lesson generalises: **"minimal disruption" is only valuable when remapping
is expensive.** For stateful sharding it means moving bytes and is the whole
point. For stateless routing with connection affinity it is close to free, and
trading it for lookup speed is correct.

## 5. Non-optimal alternatives, and why each loses

| Alternative                                                       | Verdict                                                                                                                                                                                                                                                                                       |
| :---------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`hash(key) % N`**                                               | The thing consistent hashing exists to replace. Changing `N` remaps essentially _every_ key (`(N−1)/N` of them). Fine when the node count never changes; catastrophic otherwise.                                                                                                              |
| **Hash ring, no virtual nodes**                                   | Minimal disruption, but the arcs are wildly uneven — the largest is `O(log N / N)` of the circle rather than `1/N`. Measured peak/mean above 1.5 at 12 nodes. Unusable as-is, which is why virtual nodes exist.                                                                               |
| **Hash ring, 100–1000 virtual nodes**                             | The industry default (Dynamo, Cassandra, memcached clients). Correct and minimally disruptive, but pays `O(V·N)` memory, an `O(V·N log(V·N))` re-sort on every membership change, _and_ still lands at the worst balance in the table. Superseded on every axis by AnchorHash.                |
| **Multi-probe consistent hashing** (Appleton & O'Reilly)          | Removes virtual nodes by probing `k` positions per lookup and taking the closest — `O(N)` memory instead of `O(V·N)`. A real improvement over the ring, but `k` probes per lookup and still worse balance than AnchorHash at more cost.                                                       |
| **Consistent hashing with bounded loads** (Mirrokni et al., 2016) | Adds a hard capacity cap per node, forwarding overflow to the next node on the ring. Solves a _different_ problem — worst-case overload guarantees — and composes with any of the above rather than competing with them. Worth reaching for when tail latency from hot shards is the concern. |
| **MementoHash** (2023)                                            | A more recent stateful design with minimal memory and strong benchmarks, positioned directly against AnchorHash. Genuinely competitive; the difference is small enough that AnchorHash's larger deployment record decides it here.                                                            |
| **Rendezvous with a skeleton tree**                               | Organises nodes into a tree so lookups cost `O(log N)` instead of `O(N)`, keeping the weighting. Fixes rendezvous's one weakness at the price of a structure to maintain. The right choice if exact weighting is required at scale.                                                           |

## 6. Choosing

```
Can nodes fail individually (as opposed to the pool only shrinking at the end)?
├── No -- resizable shard pool, buckets are 0..N-1
│   └────────────────────────────► JumpHash        (zero memory, perfect balance)
└── Yes
    ├── Nodes have different capacities ─► RendezvousHash  (exact weighting)
    │      ...and there are many nodes ──► rendezvous + skeleton tree
    ├── Stateless routing, remap is cheap ► MaglevHash     (fastest lookup)
    └── Stateful data, remap moves bytes ─► AnchorHash     ← the general answer
```

## 7. Complexity summary

| Algorithm        | Lookup                | Memory   | Update         | Balance (measured) | Minimal?  |
| :--------------- | :-------------------- | :------- | :------------- | -----------------: | :-------- |
| `HashRing`       | `O(log VN)`           | `O(V·N)` | `O(VN log VN)` |              1.105 | yes       |
| `JumpHash`       | `O(ln N)`             | **0**    | `O(1)`         |              1.018 | tail only |
| `RendezvousHash` | `O(N)`                | `O(N)`   | `O(1)`         |              1.017 | yes       |
| `MaglevHash`     | **`O(1)`**            | `O(M)`   | `O(M)` rebuild |              1.019 | **no**    |
| `AnchorHash`     | `O(ln(a/N))` ≈ `O(1)` | `O(a)`   | `O(1)`         |          **1.014** | yes       |

## 8. A caveat

All of these use a non-cryptographic hash. An adversary who can choose keys can
concentrate load on one node — a denial-of-service against the balance property
rather than the correctness one. If keys are attacker-controlled, use a keyed
hash with a secret seed. The structural analysis is unaffected; only `_hash_key`
needs replacing.

---

## References

- Karger, Lehman, Leighton, Panigrahy, Levine, Lewin, _Consistent hashing and random trees_, STOC 1997.
- Thaler & Ravishankar, _Using name-based mappings to increase hit rates_, IEEE/ACM ToN 6(1), 1998. (Rendezvous / HRW.)
- Lamping & Veach, [_A Fast, Minimal Memory, Consistent Hash Algorithm_](https://arxiv.org/abs/1406.2294), 2014. (Jump.)
- Eisenbud et al., _Maglev: A Fast and Reliable Software Network Load Balancer_, NSDI 2016.
- Mirrokni, Thorup, Zadimoghaddam, _Consistent Hashing with Bounded Loads_, SODA 2018 (arXiv 2016).
- Mendelson, Vargaftik, Barabash, Hay, Keslassy, Orda, [_AnchorHash: A Scalable Consistent Hash_](https://arxiv.org/abs/1812.09674), IEEE/ACM ToN 29(6), 2021.
- Coluzzi et al., [_MementoHash: A Stateful, Minimal Memory, Best Performing Consistent Hash Algorithm_](https://arxiv.org/abs/2306.09783), 2023.
- Gryski, [_Consistent Hashing: Algorithmic Tradeoffs_](https://dgryski.medium.com/consistent-hashing-algorithmic-tradeoffs-ef6b8e2fcae8). (The best short survey of this space.)
