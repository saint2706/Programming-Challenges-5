#include <algorithm>
#include <iostream>
#include <list>
#include <stdexcept>

struct Block {
    size_t start;
    size_t size;
    bool free;
};

class SimpleAllocator {
  public:
    explicit SimpleAllocator(size_t total_size) {
        blocks.push_back({0, total_size, true});
    }

    size_t allocate(size_t bytes) {
        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (it->free && it->size >= bytes) {
                size_t alloc_start = it->start;
                if (it->size > bytes) {
                    Block new_block{it->start + bytes, it->size - bytes, true};
                    it->size = bytes;
                    blocks.insert(std::next(it), new_block);
                }
                it->free = false;
                return alloc_start;
            }
        }
        throw std::runtime_error("out of memory");
    }

    void free_block(size_t start) {
        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (it->start == start && !it->free) {
                it->free = true;
                coalesce(it);
                return;
            }
        }
        throw std::runtime_error("invalid free");
    }

    void dump() const {
        for (const auto &b : blocks) {
            std::cout << "[" << b.start << ".." << (b.start + b.size) << ") " << (b.free ? "free" : "used")
                      << "\n";
        }
    }

  private:
    std::list<Block> blocks;

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
    size_t a = alloc.allocate(128);
    size_t b = alloc.allocate(256);
    alloc.free_block(a);
    size_t c = alloc.allocate(64);
    alloc.dump();
    return 0;
}
#endif
