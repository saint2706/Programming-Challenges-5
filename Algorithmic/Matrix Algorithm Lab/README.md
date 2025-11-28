# Matrix Algorithm Lab

A Python library for matrix operations, featuring both naive and advanced multiplication algorithms.

![Matrix Ops Visualization](matrix_ops_viz.gif)

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Matrix Multiplication
Given two matrices $A$ (size $m \times n$) and $B$ (size $n \times p$), the product $C = AB$ is an $m \times p$ matrix where:
$$C_{ij} = \sum_{k=1}^n A_{ik} B_{kj}$$

### Strassen's Algorithm
Strassen's algorithm divides a matrix into 4 sub-matrices and uses 7 recursive multiplications (instead of the usual 8) to compute the product.
This improves the asymptotic time complexity from $O(N^3)$ to $O(N^{\log_2 7}) \approx O(N^{2.81})$.

## 💻 Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install numpy
    ```
3.  (Optional) Install `manim` for visualization:
    ```bash
    pip install manim
    ```

## 🚀 Usage

### Basic Operations

```python
from matrix import Matrix

# Create matrices (from lists or numpy arrays)
A = Matrix([[1, 2], [3, 4]], backend="list")
B = Matrix([[2, 0], [1, 2]], backend="list")

# Addition
C = A.add(B)

# Multiplication (Naive)
D = A.naive_multiply(B)

# Multiplication (Strassen)
E = A.strassen_multiply(B)

print(E.to_list())
# Output: [[4.0, 4.0], [10.0, 8.0]]
```

### Benchmarking

```python
from matrix import benchmark_multiplication

results = benchmark_multiplication(sizes=[64, 128], backend="numpy")
for res in results:
    print(res)
```

## 📊 Complexity Analysis

| Algorithm | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Naive** | $O(N^3)$ | $O(N^2)$ |
| **Strassen** | $O(N^{2.81})$ | $O(N^2)$ (high constant factor) |

## 🎬 Demos

### Generating the Animation
To generate the matrix multiplication visualization:

```bash
manim -pql visualize_matrix_ops.py MatrixOpsDemo
```

## Demos

To demonstrate the algorithm, run:

```bash
python main.py
```
