# Approximate Set Membership (Bloom Filter)

A space-efficient probabilistic data structure that is used to test whether an element is a member of a set. False positive matches are possible, but false negatives are not.


## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

A **Bloom filter** is a data structure designed to tell you, rapidly and memory-efficiently, whether an element is present in a set. The price for this efficiency is that a Bloom filter is a **probabilistic** data structure: it tells us that the element either _definitely is not_ in the set or _may be_ in the set.

### How It Works

1.  **Initialization**: Start with a bit array of size $m$ set to all 0s.
2.  **Adding an Item**: To add an item, feed it to $k$ different hash functions. Each function maps the item to one of the $m$ array positions. Set the bits at these positions to 1.
3.  **Checking an Item**: To check if an item is in the set, feed it to the same $k$ hash functions to get $k$ positions.
    - If **any** of the bits at these positions is 0, the item is **definitely not** in the set.
    - If **all** of the bits are 1, the item is **probably** in the set (though it might be a false positive).

### Optimal Parameters

- **Size ($m$)**: Depends on the expected number of elements ($n$) and desired false positive rate ($p$).
  $$m = -\frac{n \ln p}{(\ln 2)^2}$$
- **Hash Functions ($k$)**:
  $$k = \frac{m}{n} \ln 2$$

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository (if you haven't already).
2.  Install dependencies:

    ```bash
    pip install mmh3 matplotlib numpy seaborn
    ```

## 🚀 Usage

### Basic Usage

```python
from bloom import BloomFilter

# Initialize with capacity of 1000 items and 1% false positive rate
bf = BloomFilter(capacity=1000, false_positive_rate=0.01)

# Add items
bf.add("apple")
bf.add("banana")

# Check items
print(bf.contains("apple"))   # True (Probably present)
print(bf.contains("carrot"))  # False (Definitely not present)
```

### Advanced Analysis

The module includes an analyzer to test actual performance against theoretical limits.

```python
from bloom import BloomFilterAnalyzer

analyzer = BloomFilterAnalyzer()
# Run comprehensive analysis across different capacities and error rates
analyzer.comprehensive_analysis()
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :-------- | :-------------- | :--------------- |
| **Add**   | $O(k)$          | $O(m)$           |
| **Check** | $O(k)$          | $O(m)$           |

Where:

- $k$ is the number of hash functions.
- $m$ is the size of the bit array.

**Note**: The space complexity is extremely low compared to storing the actual items. For example, for a 1% false positive rate, a Bloom filter requires only about **9.6 bits per element**, regardless of the size of the elements themselves.
