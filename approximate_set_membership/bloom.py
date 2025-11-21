"""Bloom filter tools with configurable bit arrays and benchmarking support."""
from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List

import mmh3


class BitArray:
    """A compact bit array backed by a ``bytearray``.

    The class intentionally exposes only the operations needed by the Bloom filter
    implementation so that it stays minimal and easy to reason about.
    """

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("BitArray size must be positive")
        self.size = size
        self._bytes = bytearray((size + 7) // 8)

    def __len__(self) -> int:
        return self.size

    def _index(self, bit: int) -> tuple[int, int]:
        if bit < 0 or bit >= self.size:
            raise IndexError("bit index out of range")
        byte_index, bit_offset = divmod(bit, 8)
        return byte_index, bit_offset

    def set(self, bit: int) -> None:
        byte_index, bit_offset = self._index(bit)
        self._bytes[byte_index] |= 1 << bit_offset

    def get(self, bit: int) -> bool:
        byte_index, bit_offset = self._index(bit)
        return (self._bytes[byte_index] >> bit_offset) & 1 == 1

    def clear(self) -> None:
        for i in range(len(self._bytes)):
            self._bytes[i] = 0

    def density(self) -> float:
        """Return the fraction of bits that are set."""
        set_bits = sum(bin(b).count("1") for b in self._bytes)
        return set_bits / self.size


HashFunction = Callable[[str, int], int]


def _mmh3_hash(value: str, seed: int) -> int:
    """Hash wrapper that keeps the interface uniform."""
    return mmh3.hash(value, seed, signed=False)


@dataclass
class ExperimentResult:
    size: int
    hash_count: int
    inserted: int
    queried: int
    measured_fpr: float
    theoretical_fpr: float
    insertion_time: float
    query_time: float


class BloomFilter:
    """Bloom filter with configurable size and hash count."""

    def __init__(self, size: int, hash_count: int, *, hash_function: HashFunction | None = None):
        if size <= 0:
            raise ValueError("size must be positive")
        if hash_count <= 0:
            raise ValueError("hash_count must be positive")
        self.size = size
        self.hash_count = hash_count
        self.bit_array = BitArray(size)
        self.hash_function = hash_function or _mmh3_hash
        self._seeds = [i for i in range(hash_count)]
        self.items_added = 0

    @classmethod
    def from_capacity(cls, capacity: int, false_positive_rate: float) -> "BloomFilter":
        """Create a Bloom filter using optimal parameters for a target error rate."""
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("false_positive_rate must be between 0 and 1")

        size = math.ceil(-(capacity * math.log(false_positive_rate)) / (math.log(2) ** 2))
        hash_count = max(1, round((size / capacity) * math.log(2)))
        return cls(size, hash_count)

    def _positions(self, item: str) -> Iterable[int]:
        for seed in self._seeds:
            yield self.hash_function(item, seed) % self.size

    def insert(self, item: str) -> None:
        for pos in self._positions(item):
            self.bit_array.set(pos)
        self.items_added += 1

    def contains(self, item: str) -> bool:
        return all(self.bit_array.get(pos) for pos in self._positions(item))

    def theoretical_false_positive_rate(self, items_inserted: int | None = None) -> float:
        n = items_inserted if items_inserted is not None else self.items_added
        if n == 0:
            return 0.0
        exponent = -self.hash_count * n / self.size
        return (1 - math.exp(exponent)) ** self.hash_count


def run_false_positive_experiment(
    *,
    filter_size: int,
    hash_count: int,
    insertions: int,
    queries: int,
    seed: int = 0,
    hash_function: HashFunction | None = None,
) -> ExperimentResult:
    """Insert random strings and measure the false positive rate."""

    rng = random.Random(seed)
    bf = BloomFilter(filter_size, hash_count, hash_function=hash_function)
    inserted_values = [f"item-{rng.randrange(1_000_000_000)}" for _ in range(insertions)]
    query_values = [f"probe-{rng.randrange(1_000_000_000)}" for _ in range(queries)]

    start_insert = time.perf_counter()
    for value in inserted_values:
        bf.insert(value)
    insert_duration = time.perf_counter() - start_insert

    false_hits = 0
    start_query = time.perf_counter()
    for value in query_values:
        if bf.contains(value):
            false_hits += 1
    query_duration = time.perf_counter() - start_query

    measured = false_hits / queries
    theoretical = bf.theoretical_false_positive_rate(insertions)

    return ExperimentResult(
        size=filter_size,
        hash_count=hash_count,
        inserted=insertions,
        queried=queries,
        measured_fpr=measured,
        theoretical_fpr=theoretical,
        insertion_time=insert_duration,
        query_time=query_duration,
    )


def benchmark_dataset(words: List[str], *, false_positive_rate: float = 0.01) -> ExperimentResult:
    """Benchmark the Bloom filter on a static dataset of words."""

    bloom = BloomFilter.from_capacity(len(words), false_positive_rate)
    start_insert = time.perf_counter()
    for word in words:
        bloom.insert(word)
    insert_duration = time.perf_counter() - start_insert

    # Create queries that are guaranteed misses to measure the FP rate
    queries = [f"{word}-miss" for word in words]
    false_hits = 0
    start_query = time.perf_counter()
    for word in queries:
        if bloom.contains(word):
            false_hits += 1
    query_duration = time.perf_counter() - start_query

    measured = false_hits / len(queries)
    theoretical = bloom.theoretical_false_positive_rate()

    return ExperimentResult(
        size=bloom.size,
        hash_count=bloom.hash_count,
        inserted=len(words),
        queried=len(queries),
        measured_fpr=measured,
        theoretical_fpr=theoretical,
        insertion_time=insert_duration,
        query_time=query_duration,
    )


def _format_result(result: ExperimentResult) -> str:
    return (
        f"m={result.size} bits | k={result.hash_count} | n={result.inserted} | q={result.queried}\n"
        f"Measured FPR:    {result.measured_fpr:.5f}\n"
        f"Theoretical FPR:  {result.theoretical_fpr:.5f}\n"
        f"Insert time:     {result.insertion_time * 1000:.2f} ms\n"
        f"Query time:      {result.query_time * 1000:.2f} ms"
    )


def cli(argv: List[str] | None = None) -> None:
    """Command-line interface for running experiments."""

    parser = argparse.ArgumentParser(description="Bloom filter false positive estimator")
    parser.add_argument("--size", type=int, default=10_000, help="Bit array size (m)")
    parser.add_argument("--hashes", type=int, default=4, help="Number of hash functions (k)")
    parser.add_argument("--insertions", type=int, default=2_000, help="Number of items to insert")
    parser.add_argument("--queries", type=int, default=5_000, help="Number of negative queries")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run an additional benchmark using a synthetic word list",
    )
    args = parser.parse_args(argv)

    fp_result = run_false_positive_experiment(
        filter_size=args.size,
        hash_count=args.hashes,
        insertions=args.insertions,
        queries=args.queries,
        seed=args.seed,
    )
    print("False positive experiment:\n" + _format_result(fp_result))

    if args.benchmark:
        wordlist = [f"word-{i}" for i in range(10_000)]
        bench_result = benchmark_dataset(wordlist)
        print("\nDataset benchmark:\n" + _format_result(bench_result))


if __name__ == "__main__":
    cli()
