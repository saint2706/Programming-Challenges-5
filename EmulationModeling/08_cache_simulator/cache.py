from collections import deque

class CacheLine:
    def __init__(self):
        self.valid = False
        self.tag = None
        self.data = None
        self.dirty = False

class CacheSet:
    def __init__(self, assoc, policy="LRU"):
        self.assoc = assoc
        self.policy = policy
        self.lines = [CacheLine() for _ in range(assoc)]
        # For LRU: tracking usage order. Front = MRU, Back = LRU.
        # Store indices of lines.
        self.usage_queue = deque()
        # For FIFO: Front = Oldest.

    def access(self, tag):
        # Check for hit
        for i, line in enumerate(self.lines):
            if line.valid and line.tag == tag:
                self.update_usage(i, hit=True)
                return True, i # Hit
        return False, -1 # Miss

    def update_usage(self, index, hit):
        if self.policy == "LRU":
            if hit:
                # Move to MRU (front)? Or back? Deque: append=right (new), popleft=left (old).
                # Let's say right is MRU.
                if index in self.usage_queue:
                    self.usage_queue.remove(index)
                self.usage_queue.append(index)
            else:
                # Allocation (miss) -> implicitly MRU
                self.usage_queue.append(index)
        elif self.policy == "FIFO":
            if not hit:
                self.usage_queue.append(index)

    def allocate(self, tag):
        # Find invalid line first
        for i, line in enumerate(self.lines):
            if not line.valid:
                line.valid = True
                line.tag = tag
                self.update_usage(i, hit=False)
                return

        # Evict
        if self.policy == "LRU" or self.policy == "FIFO":
            evict_idx = self.usage_queue.popleft() # Oldest/LRU
            self.lines[evict_idx].tag = tag
            self.lines[evict_idx].valid = True
            self.update_usage(evict_idx, hit=False)

class Cache:
    def __init__(self, size=1024, block_size=64, assoc=4, policy="LRU"):
        self.size = size # Total bytes
        self.block_size = block_size
        self.assoc = assoc

        self.num_lines = size // block_size
        self.num_sets = self.num_lines // assoc

        self.sets = [CacheSet(assoc, policy) for _ in range(self.num_sets)]

        self.hits = 0
        self.misses = 0

    def get_address_parts(self, address):
        # address is an integer
        offset_bits = self.block_size.bit_length() - 1 # log2(block_size)
        set_bits = self.num_sets.bit_length() - 1

        offset = address & ((1 << offset_bits) - 1)
        set_idx = (address >> offset_bits) & ((1 << set_bits) - 1)
        tag = address >> (offset_bits + set_bits)

        return tag, set_idx, offset

    def read(self, address):
        tag, set_idx, offset = self.get_address_parts(address)
        cache_set = self.sets[set_idx]

        hit, idx = cache_set.access(tag)
        if hit:
            self.hits += 1
        else:
            self.misses += 1
            cache_set.allocate(tag)

    def get_stats(self):
        total = self.hits + self.misses
        rate = (self.hits / total) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "rate": rate
        }
