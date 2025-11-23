from cache import Cache

def main():
    print("Cache Simulator")
    print("Configuration: Size=4KB, Block=64B, Assoc=4, Policy=LRU")

    cache = Cache(size=4096, block_size=64, assoc=4, policy="LRU")

    # Simulate a loop pattern
    # Array A of size 2048 bytes (32 blocks).
    # Mapped to sets?
    # 4096 / 64 = 64 lines. 64 / 4 = 16 sets.
    # Array accesses: 0, 64, 128 ...

    print("\nSimulating sequential access (stream)...")
    for addr in range(0, 4096 * 2, 64): # Access 8KB data
        cache.read(addr)

    stats = cache.get_stats()
    print(f"Hits: {stats['hits']}, Misses: {stats['misses']}, Rate: {stats['rate']:.2%}")
    # Expected: First 4KB fills cache (Misses). Next 4KB evicts (Misses).

    print("\nResetting...")
    cache = Cache(size=4096, block_size=64, assoc=4, policy="LRU")

    print("Simulating loop over 2KB array (fits in cache)...")
    base_addrs = range(0, 2048, 64)
    for _ in range(5): # 5 iterations
        for addr in base_addrs:
            cache.read(addr)

    stats = cache.get_stats()
    print(f"Hits: {stats['hits']}, Misses: {stats['misses']}, Rate: {stats['rate']:.2%}")
    # Expected: Iter 1 (32 misses). Iter 2-5 (32*4 hits).
    # Total: 32 miss, 128 hits. Rate ~80%.

if __name__ == "__main__":
    main()
