# Large Integer Arithmetic Library

A library for performing arithmetic operations on arbitrarily large integers beyond the limits of primitive integer types.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Arbitrary-precision arithmetic** allows working with integers of any size by representing them as arrays or vectors of digits.

### Algorithms Implemented

1. **Addition/Subtraction**: Schoolbook algorithm with carry/borrow propagation
2. **Multiplication**: Karatsuba algorithm for faster multiplication
3. **Division**: Long division with remainder

### Karatsuba Multiplication

A divide-and-conquer algorithm that reduces multiplication complexity:

- Split numbers: $x = a \cdot 10^m + b$, $y = c \cdot 10^m + d$
- Compute: $ac$, $bd$, $(a+b)(c+d)$
- Result: $ac \cdot 10^{2m} + ((a+b)(c+d) - ac - bd) \cdot 10^m + bd$

**Complexity**: $O(n^{1.585})$ vs. $O(n^2)$ for schoolbook

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use large_integer_arithmetic_library::BigInt;

// Create from string
let a = BigInt::from("123456789012345678901234567890");
let b = BigInt::from("987654321098765432109876543210");

// Arithmetic operations
let sum = &a + &b;
let product = &a * &b;
let quotient = &a / &b;

println!("Sum: {}", sum);
println!("Product: {}", product);
```

## 📊 Complexity Analysis

| Operation                      | Time Complexity |
| :----------------------------- | :-------------- |
| **Addition**                   | $O(n)$          |
| **Subtraction**                | $O(n)$          |
| **Multiplication (Karatsuba)** | $O(n^{1.585})$  |
| **Division**                   | $O(n^2)$        |

Where $n$ is the number of digits.
