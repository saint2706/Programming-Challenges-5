"""
Emulation/Modeling project implementation.
"""

import unittest
from cache import Cache

class TestCache(unittest.TestCase):
    """
    Docstring for TestCache.
    """
    def test_direct_mapped_hit_miss(self):
        # Size=64, Block=16, Assoc=1 (Direct Mapped)
        # 4 lines. 4 sets.
        """
        Docstring for test_direct_mapped_hit_miss.
        """
        cache = Cache(size=64, block_size=16, assoc=1)

        # Addr 0 -> Set 0. Miss.
        cache.read(0)
        self.assertEqual(cache.misses, 1)
        self.assertEqual(cache.hits, 0)

        # Addr 0 -> Set 0. Hit.
        cache.read(0)
        self.assertEqual(cache.hits, 1)

        # Addr 16 -> Set 1. Miss.
        cache.read(16)
        self.assertEqual(cache.misses, 2)

        # Addr 64 (Binary: 100 0000). Block bits=4. Set bits=2 (4 sets).
        # 64 / 16 = 4. 4 % 4 = 0. Set 0.
        # Tag differs. Conflict miss. Evicts Addr 0.
        cache.read(64)
        self.assertEqual(cache.misses, 3)

        # Read 0 again -> Miss.
        cache.read(0)
        self.assertEqual(cache.misses, 4)

    def test_assoc_lru(self):
        # Size=64, Block=16, Assoc=2.
        # 4 lines. 2 sets.
        """
        Docstring for test_assoc_lru.
        """
        cache = Cache(size=64, block_size=16, assoc=2, policy="LRU")

        # Set 0 addresses: 0, 32, 64, 96... (Step 32)

        cache.read(0)  # Miss. Set 0 has [0, ?]
        cache.read(32) # Miss. Set 0 has [0, 32]

        cache.read(0)  # Hit. MRU=0. Set 0 has [32, 0] (conceptually)

        cache.read(64) # Miss. Evicts LRU (32). Set 0 has [0, 64]

        cache.read(32) # Miss. Evicts LRU (0). Set 0 has [64, 32]

        self.assertEqual(cache.misses, 4)
        self.assertEqual(cache.hits, 1)

if __name__ == '__main__':
    unittest.main()
