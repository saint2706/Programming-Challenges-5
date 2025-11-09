#!/usr/bin/env python3
"""
Minimal Bloom filter demo
pip install mmh3  # optional, falls back to pure-python hash family
"""

import math, random, string, sys
from array import array

try:
    import mmh3                       # fast, high-quality
    _HAVE_MMH3 = True
except ModuleNotFoundError:
    _HAVE_MMH3 = False

# ------------------------------------------------------------------
# Bit array (pure Python, memory compact)
# ------------------------------------------------------------------
class BitArray:
    """Fixed-size bit vector using Python std-lib only."""
    def __init__(self, num_bits: int):
        self.n = num_bits
        self.arr = array('Q', [0]) * ((num_bits + 63) // 64)   # 64-bit words

    def _index(self, pos: int):
        return pos >> 6, pos & 63                               # word, bit

    def set(self, pos: int):
        w, b = self._index(pos)
        self.arr[w] |= 1 << b

    def get(self, pos: int) -> bool:
        w, b = self._index(pos)
        return (self.arr[w] >> b) & 1

    def density(self) -> float:
        """Return fraction of 1-bits (for visualisation)."""
        ones = sum(bin(q).count('1') for q in self.arr)
        return ones / self.n


# ------------------------------------------------------------------
# Hash factory
# ------------------------------------------------------------------
class Hasher:
    """Return k different 64-bit hashes for a key."""
    def __init__(self, k: int, seed: int = 0):
        self.k = k
        self.seed = seed

    def hashes(self, key: bytes) -> list[int]:
        raise NotImplementedError


class MMH3Hasher(Hasher):
    def hashes(self, key: bytes) -> list[int]:
        return [mmh3.hash(key, self.seed + i, signed=False) for i in range(self.k)]


class FNVHasher(Hasher):
    """Fast, decent 64-bit hashes using FNV-style multiply-xor."""
    def __init__(self, k: int, seed: int = 0):
        super().__init__(k, seed)
        self.offsets = [hash((self.seed + i).to_bytes(4, 'little')) & 0xFFFF_FFFF_FFFF_FFFF
                        for i in range(k)]

    def hashes(self, key: bytes) -> list[int]:
        h = int.from_bytes(key, 'little') & 0xFFFF_FFFF_FFFF_FFFF
        out = []
        for off in self.offsets:
            h = (h ^ off) * 0x100000001b3 & 0xFFFF_FFFF_FFFF_FFFF
            out.append(h)
        return out


# ------------------------------------------------------------------
# Bloom filter
# ------------------------------------------------------------------
class BloomFilter:
    def __init__(self, expected_items: int, fp_rate: float,
                 hasher_factory=MMH3Hasher if _HAVE_MMH3 else FNVHasher):
        self.n = expected_items
        self.p = fp_rate
        self.m = self._optimal_m()
        self.k = self._optimal_k()
        self.bits = BitArray(self.m)
        self.hasher = hasher_factory(self.k)

    # Formulas: m = - n ln p / (ln 2)^2   and   k = m/n ln 2
    def _optimal_m(self) -> int:
        return int(-self.n * math.log(self.p) / (math.log(2) ** 2)) + 1

    def _optimal_k(self) -> int:
        return max(1, int(self.m / self.n * math.log(2) + 0.5))

    def add(self, key: str | bytes):
        if isinstance(key, str):
            key = key.encode('utf8')
        for h in self.hasher.hashes(key):
            self.bits.set(h % self.m)

    def __contains__(self, key: str | bytes):
        if isinstance(key, str):
            key = key.encode('utf8')
        for h in self.hasher.hashes(key):
            if not self.bits.get(h % self.m):
                return False
        return True

    def theoretical_fp(self) -> float:
        """After n insertions."""
        return (1 - math.exp(-self.k * self.n / self.m)) ** self.k


# ------------------------------------------------------------------
# Tiny test bench
# ------------------------------------------------------------------
def randstr(n=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def demo():
    N, P = 100_000, 0.01          # expect 1 % false positives
    bf = BloomFilter(N, P)
    print(f"Bloom filter: m={bf.m:,} bits  k={bf.k}  target FP={P:.2%}")

    # Insert phase
    inserted = {randstr() for _ in range(N)}
    for w in inserted:
        bf.add(w)

    # Query phase
    queries = {randstr() for _ in range(50_000)} - inserted   # guarantee negatives
    fps = sum(q in bf for q in queries)
    emp_fp = fps / len(queries)
    theo_fp = bf.theoretical_fp()
    print(f"Empirical FP: {emp_fp:.3%}   (theoretical {theo_fp:.3%})")

    # Visualise bit density
    print("Bit density heat map (every 64th bit shown, # = ≥50 % ones)")
    vis = ""
    for i in range(0, bf.m, 64):
        ones = sum(bf.bits.get(j) for j in range(i, min(i + 64, bf.m)))
        vis += "#" if ones >= 32 else "."
    print(vis)

if __name__ == '__main__':
    demo()
