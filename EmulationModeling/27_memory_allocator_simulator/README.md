# Memory Allocator Simulator

A simulation of a memory allocator using a free-list mechanism to manage dynamic memory allocation (`malloc` and `free`).

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Heap Management

Memory is treated as a large contiguous block.

- **Allocation**: Finds a free block of sufficient size. Strategies include First-Fit, Best-Fit, and Worst-Fit.
- **Deallocation**: Marks a block as free.
- **Coalescing**: Merges adjacent free blocks to reduce fragmentation.

### Block Structure

Each block contains a header with:

- `size`: Size of the payload.
- `is_free`: Status flag.
- `next`: Pointer to the next block in the list.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DMEM_ALLOC_DEMO main.cpp -o mem_alloc
./mem_alloc
```

### API

```cpp
MemoryAllocator allocator(1024); // 1KB heap

void* ptr1 = allocator.allocate(100);
allocator.deallocate(ptr1);
```

## 📊 Complexity Analysis

| Operation      | Complexity | Description                               |
| :------------- | :--------- | :---------------------------------------- |
| **Allocate**   | $O(N)$     | Linear scan of the free list (First-Fit). |
| **Deallocate** | $O(N)$     | May require scanning to coalesce.         |

_Where $N$ is the number of memory blocks._

## 🎬 Demos

The demo simulates allocating and freeing various blocks and prints the state of the heap to visualize fragmentation and coalescing.
