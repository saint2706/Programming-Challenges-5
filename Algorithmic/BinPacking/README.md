# Bin Packing Variants

Implementations of various bin packing algorithms and heuristics for efficiently packing items into bins.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Bin packing** places items of various sizes into a finite number of bins, minimizing the number of bins used.

### Problem Variants

1. **1D Bin Packing**: Items and bins have one dimension (size)
2. **2D Bin Packing**: Items are rectangles (width × height)
3. **3D Bin Packing**: Items are boxes (width × height × depth)

### Heuristics (1D)

#### 1. First Fit (FF)

- Place item in first bin that fits
- Time: $O(n^2)$
- Approximation: Uses at most $\lceil 1.7 \cdot OPT \rceil$ bins

#### 2. Best Fit (BF)

- Place item in bin with least remaining space that fits
- Time: $O(n \log n)$ with heap
- Often better than FF in practice

#### 3. First Fit Decreasing (FFD)

- Sort items by size (descending)
- Apply First Fit
- Time: $O(n \log n)$
- Approximation: Uses at most $\lceil \frac{11}{9} \cdot OPT \rceil + 4$ bins

#### 4. Next Fit (NF)

- Place item in current bin if it fits, else open new bin
- Time: $O(n)$
- Approximation: Uses at most $2 \cdot OPT$ bins

### 2D Bin Packing

Additional complexity: must consider orientation and placement strategy.

- **Shelf algorithms**: Pack items in horizontal shelves
- **Guillotine cut**: Use rectangular cuts only

## 💻 Installation

```bash
go build ./cmd/binpacking
go test
```

## 🚀 Usage

### 1D Bin Packing

```go
package main

import (
    "fmt"
    "binpacking"
)

func main() {
    items := []int{7, 5, 6, 4, 2, 3, 7, 5}
    binCapacity := 10

    // First Fit Decreasing
    bins := binpacking.FirstFitDecreasing(items, binCapacity)
    fmt.Printf("FFD uses %d bins\n", len(bins))

    // Best Fit
    bins = binpacking.BestFit(items, binCapacity)
    fmt.Printf("BF uses %d bins\n", len(bins))
}
```

### 2D Bin Packing

```go
type Rectangle struct {
    Width, Height int
}

items := []Rectangle{
    {Width: 5, Height: 3},
    {Width: 2, Height: 8},
    {Width: 4, Height: 4},
}

binWidth, binHeight := 10, 10
bins := binpacking.Pack2D(items, binWidth, binHeight)
```

## 📊 Complexity Analysis

| Algorithm     | Time Complexity | Approximation Ratio |
| :------------ | :-------------- | :------------------ |
| **First Fit** | $O(n^2)$        | 1.7 × OPT           |
| **Best Fit**  | $O(n \log n)$   | 1.7 × OPT           |
| **FFD**       | $O(n \log n)$   | 1.22 × OPT          |
| **Next Fit**  | $O(n)$          | 2 × OPT             |

**Note**: Optimal bin packing is NP-hard, so these heuristics provide good practical solutions.
