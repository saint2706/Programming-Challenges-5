#include <algorithm>
#include <iostream>
#include <list>
#include <stdexcept>
#include <unordered_map>

struct Block {
    size_t start;
    size_t size;
    bool free;
};

// A simple best-fit allocator with coalescing and basic validation of
// double-frees/out-of-bounds frees. Alignment defaults to 8 bytes.
class SimpleAllocator {
  public:
    explicit SimpleAllocator(size_t total_size, size_t alignment = 8) : align(alignment) {
        if (alignment == 0 || (alignment & (alignment - 1)) != 0)
            throw std::invalid_argument("alignment must be a power of two");
        blocks.push_back({0, total_size, true});
    }

    size_t allocate(size_t bytes) {
        const size_t need = align_up(bytes);
        auto fit = blocks.end();
        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (it->free && it->size >= need) {
                if (fit == blocks.end() || it->size < fit->size)
                    fit = it;
            }
        }
        if (fit == blocks.end())
            throw std::runtime_error("out of memory");

        const size_t alloc_start = fit->start;
        const size_t remainder = fit->size - need;
        fit->size = need;
        fit->free = false;
        allocations[alloc_start] = need;
        if (remainder > 0) {
            blocks.insert(std::next(fit), Block{alloc_start + need, remainder, true});
        }
        return alloc_start;
    }

    void free_block(size_t start) {
        auto alloc_it = allocations.find(start);
        if (alloc_it == allocations.end())
            throw std::runtime_error("invalid or double free");

        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (it->start == start && !it->free) {
                it->free = true;
                allocations.erase(alloc_it);
                coalesce(it);
                return;
            }
        }
        throw std::runtime_error("corrupted free list");
    }

    void dump() const {
        for (const auto &b : blocks) {
            std::cout << "[" << b.start << ".." << (b.start + b.size) << ") " << (b.free ? "free" : "used")
                      << " size=" << b.size << "\n";
        }
    }

    size_t free_bytes() const {
        size_t total = 0;
        for (const auto &b : blocks) {
            if (b.free)
                total += b.size;
        }
        return total;
    }

  private:
    size_t align;
    std::list<Block> blocks;
    std::unordered_map<size_t, size_t> allocations;

    size_t align_up(size_t value) const { return (value + align - 1) & ~(align - 1); }

    void coalesce(std::list<Block>::iterator it) {
        if (it != blocks.begin()) {
            auto prev = std::prev(it);
            if (prev->free && prev->start + prev->size == it->start) {
                prev->size += it->size;
                it = blocks.erase(it);
                it = prev;
            }
        }
        auto next = std::next(it);
        if (next != blocks.end() && next->free && it->start + it->size == next->start) {
            it->size += next->size;
            blocks.erase(next);
        }
    }
};

#ifdef ALLOCATOR_DEMO
int main() {
    SimpleAllocator alloc(1024);
    size_t a = alloc.allocate(123);
    size_t b = alloc.allocate(200);
    alloc.free_block(a);
    size_t c = alloc.allocate(64);
    std::cout << "Allocated blocks at: " << a << ", " << b << ", " << c << "\n";
    alloc.dump();
    return 0;
}
#endif
