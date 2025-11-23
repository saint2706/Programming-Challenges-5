# Cache Simulator

A simulator for CPU cache memory supporting different mapping strategies and replacement policies.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Cache Policies](#cache-policies)

## 🧠 Theory

### Memory Hierarchy
Modern computers use a hierarchy of memory:
```
CPU → L1 Cache → L2 Cache → L3 Cache → Main Memory
     (fastest)                            (slowest)
```

### Cache Operation
- **Hit**: Data found in cache (fast access)
- **Miss**: Data not in cache (fetch from memory)
- **Hit Rate**: Percentage of accesses that hit
- **Locality**: Programs access nearby memory (temporal and spatial)

### Cache Structure
- **Block/Line**: Unit of data transfer (e.g., 64 bytes)
- **Set**: Group of cache lines
- **Tag**: Identifies which memory block is cached
- **Valid Bit**: Indicates if line contains valid data

## 💻 Installation

Requires Python 3.8+ (no external dependencies):
```bash
cd EmulationModeling/08_cache_simulator
python main.py
```

## 🚀 Usage

### Running Simulation
```bash
python main.py
```

The simulator runs memory access traces and reports hit/miss statistics for different cache configurations.

### Example Configuration
```python
# Configure a 4-way set-associative cache
cache = Cache(
    size=1024,           # Total cache size in bytes
    block_size=64,       # Bytes per cache line
    associativity=4      # 4-way set-associative
)

# Run trace
for address in memory_accesses:
    cache.access(address)
```

## 🗂 Cache Policies

### Mapping Strategies

#### Direct-Mapped
- Each memory block maps to exactly one cache line
- Fast and simple
- Higher conflict misses

#### Fully-Associative
- Any memory block can go in any cache line
- Flexible, fewer conflicts
- Slower, more complex hardware

#### Set-Associative (N-way)
- Compromise between direct and fully-associative
- Memory blocks map to a set, any line within set
- Common: 2-way, 4-way, 8-way

### Replacement Policies

#### LRU (Least Recently Used)
- Replace the line not used for longest time
- Good performance, matches temporal locality
- Requires tracking access order

#### FIFO (First-In-First-Out)
- Replace the oldest line in cache
- Simple to implement
- May evict frequently used blocks

#### Random
- Replace random line
- Simplest, no bookkeeping
- Surprisingly effective in practice

## 📊 Performance Metrics

### Hit Rate
```
Hit Rate = Hits / (Hits + Misses)
```

### Miss Types
- **Compulsory**: First access to block (cold start)
- **Capacity**: Cache too small for working set
- **Conflict**: Multiple blocks map to same location

## ✨ Features

- Multiple mapping strategies
- Different replacement policies
- Configurable cache parameters (size, associativity, block size)
- Memory access trace simulation
- Detailed hit/miss statistics
