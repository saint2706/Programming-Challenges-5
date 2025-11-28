# Parallel Sort Library

A parallel sorting library implementing merge sort with goroutines for efficient multi-core sorting.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Parallel sorting** divides the sorting workload across multiple processors to achieve better performance on multi-core systems.

### Parallel Merge Sort
1. **Divide**: Split array into subarrays
2. **Conquer**: Sort subarrays in parallel using goroutines
3. **Merge**: Combine sorted subarrays

### Implementation Strategy
- Use goroutines for parallel execution
- Threshold: Below certain size, use sequential sort (overhead not worth it)
- Synchronization: Use channels or wait groups

### When to Use Parallel Sort
- **Large datasets** (>100K elements)
- **Multi-core systems** available
- **CPU-bound** sorting (not I/O limited)

**Note**: For small arrays, sequential sort is faster due to goroutine overhead.

## 💻 Installation

```bash
go build ./cmd/sort
go test
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "parallelsort"
)

func main() {
    data := []int{64, 34, 25, 12, 22, 11, 90, 88, 45, 50}
    
    // Parallel sort with 4 workers
    sorted := parallelsort.Sort(data, 4)
    
    fmt.Println("Sorted:", sorted)
}
```

### Performance Comparison

```go
package main

import (
    "sort"
    "time"
)

func benchmark() {
    data := generateRandomData(10_000_000)
    
    // Sequential
    start := time.Now()
    sort.Ints(data)
    fmt.Printf("Sequential: %v\n", time.Since(start))
    
    // Parallel
    start = time.Now()
    parallelsort.Sort(data, 8)
    fmt.Printf("Parallel (8 cores): %v\n", time.Since(start))
}
```

## 📊 Complexity Analysis

| Metric | Sequential | Parallel (p cores) |
| :--- | :--- | :--- |
| **Time** | $O(n \log n)$ | $O(\frac{n \log n}{p})$ |
| **Space** | $O(n)$ | $O(n)$ |

**Speedup**: Theoretical maximum is $p$ (number of cores), but overhead reduces this to typically $0.5p$ to $0.8p$.

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
