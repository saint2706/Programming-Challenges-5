# Optimal Solution: Top-K Frequent Items in Stream

**Challenge:** find the most frequent items in a stream using bounded memory.

**Short answer:** there is no single optimal structure, because there are three
incomparable guarantees on offer. **Misra-Gries** is provably space-optimal and
uniquely _mergeable_. **Space-Saving with the bucket structure** gives the same
bound with better estimates and `O(1)` **worst-case** updates — the version
usually written scans all `k` counters and is `O(k)`. **HeavyKeeper** wins on
streams with a heavy tail and, measured here, _loses_ on heavily skewed ones.
Implementation: [`optimal_topk.py`](optimal_topk.py).

---

## 1. Three guarantees, not one problem

| Structure             | Guarantee                                  | Mergeable | Update cost           |
| :-------------------- | :----------------------------------------- | :-------: | :-------------------- |
| `MisraGries`          | never over-counts; error ≤ `N/k`           |  **yes**  | `O(1)` amortised      |
| `StreamSummary`       | never under-counts; error ≤ recorded bound |    no     | **`O(1)` worst case** |
| `UnbiasedSpaceSaving` | unbiased in expectation                    |    no     | `O(1)` worst case     |
| `HeavyKeeper`         | none — top-k heuristic                     |    no     | `O(depth)`            |

`Θ(1/ε)` counters is a **matching lower bound** for the deterministic
`ε·N`-additive guarantee, so Misra-Gries and Space-Saving are space-optimal and
nothing will improve on them under that guarantee. Improvements have to come
from changing the guarantee, which is exactly what the other two do.

## 2. The optimisation that matters: `O(1)` worst case, not `O(k)`

Space-Saving's rule is: on a miss with the table full, evict the item with the
**smallest count** and give its slot to the newcomer. The obvious implementation
scans all `k` counters to find that minimum — so every eviction is `O(k)`, and
on a stream with a long tail, nearly every arrival is an eviction.

The original paper's Stream-Summary structure fixes this by grouping counters
into **buckets by count**, kept in ascending order. The minimum is then the
first bucket, `O(1)` to reach.

**The invariant that makes it work** is worth stating, because it is what
removes the last search:

> An emptied minimum bucket is always succeeded by the bucket immediately above
> it.

Items leave a bucket only by being incremented into the next one, and an
eviction places the newcomer at `min_count + 1`. So when `buckets[min_count]`
empties, `buckets[min_count + 1]` is guaranteed non-empty and the minimum
advances by exactly one — a single increment, never a search. Without that
observation you end up writing `min(self.buckets)` and silently reintroducing
the `O(k)` scan you were trying to remove. (The first draft of this module did
exactly that, in two places.)

`test_space_saving_bucket_invariant_holds_throughout` re-checks the invariant
after every single update on a deliberately churn-heavy stream.

The result is `O(1)` **worst case**, which is the point: in a packet-processing
path the constraint is tail latency, not mean latency, and an amortised bound is
no help when the `O(k)` case lands on the packet you care about.

## 3. Measured comparison

Zipf(1.1) stream, 500 000 elements over 20 000 distinct items, 200 counters
each, recovering the true top 50:

| Structure           |    Recall | Error on kept items | Bias (incl. misses) | Counters used |
| :------------------ | --------: | ------------------: | ------------------: | ------------: |
| MisraGries          |     84.0% |              57.24% |             −64.08% |            96 |
| StreamSummary       |     84.0% |           **3.40%** |             −13.15% |           200 |
| UnbiasedSpaceSaving |     86.0% |               4.09% |             −10.50% |           200 |
| HeavyKeeper         | **88.0%** |              37.19% |             −44.73% |        **50** |

Throughput, 1 000 000 elements:

| Structure           |   Time |        Rate |
| :------------------ | -----: | ----------: |
| MisraGries          | 0.26 s | **3.8 M/s** |
| UnbiasedSpaceSaving | 0.79 s |     1.3 M/s |
| StreamSummary       | 0.86 s |     1.2 M/s |
| HeavyKeeper         | 3.47 s |    0.29 M/s |

Two notes on reading this. Misra-Gries's large "error" is not a defect — it is
the guarantee working as designed: it reports a _lower bound_, and on a stream
this long the `N/k` slack is genuinely large. Its speed advantage is real but
partly an artefact of holding fewer counters.

**Recall and estimation error are measured separately, deliberately.** Scoring
an item the structure never retained as a "−100% error" folds a recall failure
into the error statistic and hides which of the two actually went wrong.

## 4. Two findings that contradict the received claims

### HeavyKeeper's advantage is conditional on skew

HeavyKeeper is published with a headline of roughly three orders of magnitude
error reduction at equal memory. Measured on Zipfian streams over 5 000 items
with a 64-cell budget, over 8 seeds each:

| Zipf skew | HeavyKeeper recall | Space-Saving recall |    HK wins |
| --------: | -----------------: | ------------------: | ---------: |
|       1.0 |          **0.797** |               0.734 | **7 of 8** |
|       1.1 |              0.781 |           **0.852** |     3 of 8 |
|       1.3 |              0.820 |           **0.992** |     0 of 8 |

**HeavyKeeper wins on lightly skewed streams and loses on heavily skewed ones**,
and the mechanism explains why. Decay exists to stop a noisy tail from evicting
real heavy hitters. Where the tail is heaviest relative to the head, that is
exactly the failure mode and decay fixes it. Where the head already dominates,
Space-Saving retains the top items effortlessly and its exact counting is simply
more accurate than a decayed approximation.

So the right framing is not "HeavyKeeper is more accurate" but **"HeavyKeeper is
robust to tail noise"** — which is precisely the regime network telemetry (its
motivating application) lives in, and not the regime a Zipf(1.3) benchmark
occupies. The first version of the test asserted an unconditional win and
failed; the assertion now encodes the measured, conditional behaviour.

### Unbiased Space-Saving's unbiasedness is not measurable here

Ting's variant replaces deterministic eviction with a coin: keep the incumbent
with probability `c/(c+1)`, replace it with probability `1/(c+1)`. The
theoretical result is real — the counts become an unbiased estimator, equivalent
to a priority sample.

Attempting to measure it:

|                     | Mean bias | Standard error |
| :------------------ | --------: | -------------: |
| SpaceSaving         |    +1.03% |         ±5.26% |
| UnbiasedSpaceSaving |    +2.17% |         ±4.98% |

24 independent runs, scored at the eviction boundary (the genuine top items are
never evicted and are exact under both schemes, so the difference cannot appear
there). **Both are indistinguishable from zero, and from each other**: the
estimator variance is an order of magnitude larger than the bias being sought.

This is worth recording rather than quietly omitting. The reason to choose the
unbiased variant is the _guarantee_ — that summing or averaging many estimates
will not accumulate a systematic drift — not an accuracy improvement you will
observe on any single stream. Anyone choosing it expecting visibly better
numbers will be disappointed.

## 5. Mergeability: the property only Misra-Gries has

Two Misra-Gries summaries can be combined into a summary of the concatenated
streams with the same error bound: add the counters, subtract the `(k)`-th
largest value, drop the non-positive entries (Agarwal et al. 2012). Verified in
the demo: a merged summary and a single-pass summary agree on 10 of 10 top items.

This is not a nicety. It is what makes distributed aggregation possible — each
shard summarises its own traffic and only the summaries cross the network.
Space-Saving and HeavyKeeper have no sound merge operation, so a distributed
deployment must either ship raw streams or accept unquantified error. **If the
system is distributed, mergeability usually decides the choice on its own**,
regardless of the single-node numbers in section 3.

## 6. Non-optimal alternatives, and why each loses

| Alternative                                           | Verdict                                                                                                                                                                                                                                                                                                                                                           |
| :---------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exact counting with a hash map**                    | Correct, and `O(distinct)` memory — which is the entire problem. Right whenever the distinct count is small enough to fit; every structure here is a concession to it not being.                                                                                                                                                                                  |
| **Sorting the stream**                                | Correct and `O(N log N)` time with `O(N)` memory. Not a streaming algorithm at all.                                                                                                                                                                                                                                                                               |
| **Naive Space-Saving** (the current `misra_gries.py`) | Same algorithm, `O(k)` per eviction from scanning for the minimum. The bucket structure makes it `O(1)` worst case for a few extra lines. Strictly dominated.                                                                                                                                                                                                     |
| **Count-Min Sketch**                                  | Sublinear in the number of _distinct items_ rather than requiring `k` counters, and mergeable. But it only estimates the frequency of an item you name — it cannot enumerate the heavy hitters — so it needs a companion heap and a pass to know what to ask about. Its error is `ε·N` in `L1`, no better than Misra-Gries, at more space for the same guarantee. |
| **Count Sketch**                                      | Gives an `L2` guarantee, which is strictly stronger and much better on skewed data. The right choice when items just below the top matter. Costs `O(ε⁻²)` space against Misra-Gries's `O(ε⁻¹)`, and estimates are two-sided.                                                                                                                                      |
| **Lossy Counting** (Manku & Motwani)                  | Same `ε·N` guarantee, historically important, and empirically dominated by Space-Saving on both accuracy and speed in every published comparison.                                                                                                                                                                                                                 |
| **Sticky Sampling**                                   | Probabilistic, weaker guarantee than Lossy Counting at comparable space. Superseded.                                                                                                                                                                                                                                                                              |
| **Sampling then exact counting**                      | Simple and unbiased, but recovering the top `k` reliably needs a sampling rate high enough that the sample is no longer small. Loses badly to any counter-based scheme at equal memory.                                                                                                                                                                           |
| **`collections.Counter` + `most_common`**             | Exact counting again, with the same unbounded memory. The correct answer whenever it fits — and the thing to check before reaching for any of the above.                                                                                                                                                                                                          |

### Deliberately not implemented

**BPTree** (Braverman et al., 2017) is the space-optimal algorithm for the `L2`
heavy-hitters problem — `O(ε⁻² log(1/ε))` words, which is optimal — and is the
genuine frontier here. It is a considerably heavier construction (a
Bernoulli-process tree over a `CountSketch` substrate) and solves a different
problem from the one this challenge poses: the `L1` guarantee is what "find
items occurring more than `N/k` times" asks for, and that is already at its
lower bound.

**Elastic Sketch** (SIGCOMM 2018) splits the stream into a heavy part and a
light part and is the strongest general-purpose measurement sketch. It is a
composition of several structures rather than a single algorithm, which puts it
outside the scope of a reference implementation.

## 7. Choosing

```
Does the distinct count fit in memory?
└── Yes ──────────────────────────► collections.Counter (exact; check this first)

Is the system distributed?
└── Yes ──────────────────────────► MisraGries          (only mergeable option)

Do the counts feed a downstream aggregate?
└── Yes ──────────────────────────► UnbiasedSpaceSaving (no systematic drift)

Does the stream have a long noisy tail (low skew)?
├── Yes ──────────────────────────► HeavyKeeper         (robust to eviction churn)
└── No, the head dominates ───────► StreamSummary       ← the general answer
```

## 8. Complexity summary

| Structure             | Update                | Space                  | Query top-k  |
| :-------------------- | :-------------------- | :--------------------- | :----------- |
| `MisraGries`          | `O(1)` amortised      | `O(k)`                 | `O(k log k)` |
| `StreamSummary`       | **`O(1)` worst case** | `O(k)`                 | `O(k log k)` |
| `UnbiasedSpaceSaving` | `O(1)` worst case     | `O(k)`                 | `O(k log k)` |
| `HeavyKeeper`         | `O(depth)`            | `O(width · depth + k)` | `O(k log k)` |

---

## References

- Misra & Gries, _Finding repeated elements_, Science of Computer Programming 2, 1982.
- Metwally, Agrawal, El Abbadi, _Efficient computation of frequent and top-k elements in data streams_, ICDT 2005. (Space-Saving and Stream-Summary.)
- Manku & Motwani, _Approximate frequency counts over data streams_, VLDB 2002. (Lossy Counting.)
- Cormode & Muthukrishnan, _An improved data stream summary: the count-min sketch_, J. Algorithms 55, 2005.
- Charikar, Chen, Farach-Colton, _Finding frequent items in data streams_, ICALP 2002. (Count Sketch, `L2`.)
- Agarwal, Cormode, Huang, Phillips, Wei, Yi, _Mergeable summaries_, PODS 2012.
- Ting, _Data sketches for disaggregated subset sum and frequent item estimation_, SIGMOD/KDD 2018. (Unbiased Space-Saving.)
- Gong, Yang, Zhang et al., [_HeavyKeeper: An Accurate Algorithm for Finding Top-k Elephant Flows_](https://www.usenix.org/conference/atc18/presentation/gong), USENIX ATC 2018; extended in IEEE/ACM ToN 27(5), 2019.
- Braverman, Chestnut, Ivkin, Nelson, Wang, Woodruff, _BPTree: an ℓ₂ heavy hitters algorithm using constant memory_, PODS 2017.
- Cormode & Hadjieleftheriou, _Finding frequent items in data streams_, VLDB 2008. (The comparison study.)
