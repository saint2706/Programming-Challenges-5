# HyperLogLog Implementation

A probabilistic data structure for estimating the cardinality (distinct count) of a set using minimal memory.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

**HyperLogLog** is a probabilistic cardinality estimation algorithm that provides excellent accuracy with very small memory usage. It's widely used in big data systems to count unique items in massive datasets.

### How It Works
1. **Initialization**: Create $m$ registers (buckets) initialized to 0, where $m = 2^b$ for some precision parameter $b$.
2. **Hashing**: For each item, compute its hash value.
3. **Register Update**: 
   - Use the first $b$ bits of the hash to select a register
   - Count the number of leading zeros in the remaining bits (plus 1)
   - Store the maximum count seen in that register
4. **Estimation**: Use the harmonic mean of the register values, corrected by a constant $\alpha_m$.

### Key Properties
- **Space Complexity**: Only $m$ registers, typically requiring a few kilobytes
- **Accuracy**: Standard error of approximately $1.04/\sqrt{m}$
- **For $m = 2^{14}$ (16,384 registers)**: ~1.6% error, using only 16KB

### Formula
$$\text{Estimate} = \alpha_m \cdot m^2 \cdot \left(\sum_{i=1}^{m} 2^{-M[i]}\right)^{-1}$$

Where $M[i]$ is the value in the $i$-th register.

## 💻 Installation

Ensure you have Rust 1.70+ installed.

### Building the Library

```bash
cargo build --release
```

### Running Tests

```bash
cargo test
```

## 🚀 Usage

### Basic Usage

```rust
use hyperloglog_implementation::HyperLogLog;

// Create a HyperLogLog with 1% error rate
let mut hll = HyperLogLog::new(0.01);

// Add items
hll.add(&"apple");
hll.add(&"banana");
hll.add(&"apple");  // Duplicate

// Estimate cardinality
let estimate = hll.estimate();
println!("Estimated unique items: {}", estimate);
// Output: ~2
```

### Large-Scale Example

```rust
use hyperloglog_implementation::HyperLogLog;

let mut hll = HyperLogLog::new(0.01);

// Add millions of items
for i in 0..1_000_000 {
    hll.add(&format!("item_{}", i));
}

let estimate = hll.estimate();
println!("Estimated: {}, Actual: 1000000", estimate);
// Typically within 1-2% of actual value
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Add** | $O(1)$ | $O(m)$ |
| **Estimate** | $O(m)$ | $O(m)$ |

Where:
- $m$ is the number of registers (typically $2^{10}$ to $2^{16}$)

**Memory Efficiency**: For 1% error rate with 16,384 registers:
- HyperLogLog: ~16KB
- Exact counting with hash set: Gigabytes for millions of items

## 🎬 Demos

### Running the Demo

```bash
cargo run --example demo
```

This demonstrates:
1. **Basic functionality** with small datasets
2. **Accuracy testing** with known cardinalities
3. **Performance** with large-scale data
4. **Error rate analysis** across different configurations

### Expected Output

```
Adding 1000 unique items...
Actual: 1000, Estimated: 998, Error: 0.20%

Adding 1 million unique items...
Actual: 1000000, Estimated: 1015234, Error: 1.52%
```

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
