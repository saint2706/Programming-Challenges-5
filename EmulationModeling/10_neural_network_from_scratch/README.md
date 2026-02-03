# Neural Network From Scratch

A pure NumPy implementation of a feedforward neural network with manual backpropagation.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)

## 🧠 Theory

### Core Components

The implementation is a sequence of layers:
- **Linear**: affine transformation `y = xW + b`
- **ReLU**: non-linear activation
- **Sigmoid**: outputs probabilities for binary classification
- **MSELoss**: measures prediction error

Backpropagation applies the chain rule to propagate gradients backward through each layer, updating weights with gradient descent.

### Ideal Example Test Case (Exercises Edge Cases)

Use a tiny dataset that forces non-linearity, uses both classes, and includes borderline points:

**Inputs (x1, x2) → label**
1. (0.0, 0.0) → 0
2. (1.0, 0.0) → 1
3. (0.0, 1.0) → 1
4. (1.0, 1.0) → 0

This is the XOR pattern, which a purely linear model cannot solve. It forces the network to use the hidden layers and activations.

### Step-by-Step Walkthrough

#### 1) Forward Pass
- Each input vector passes through **Linear → ReLU → Linear → ReLU → Linear → Sigmoid**.
- The final sigmoid output is a value in (0,1), interpreted as class probability.

#### 2) Loss Computation
- For each sample, compute **MSE**: `(pred − target)^2`.
- The overall loss is the mean across samples.

#### 3) Backward Pass
- Compute gradient of the loss with respect to the sigmoid output.
- Backpropagate through the final Linear layer.
- Apply ReLU gradient masking (negative activations pass 0 gradient).
- Continue backward through earlier layers.

#### 4) Parameter Updates
- Each weight and bias is updated: `param = param − lr * grad`.
- The XOR pattern gradually separates because the hidden layers learn a non-linear decision boundary.

#### 5) Edge Case Handling
- **Zero input (0,0):** ensures biases matter; without biases, activations could stall.
- **Symmetry (1,0) vs (0,1):** tests whether the network can represent symmetry.
- **Conflicting corners:** forces the network to discover a non-linear split.

## 💻 Installation

Requires Python 3.8+ and NumPy:

```bash
pip install numpy
```

## 🚀 Usage

```bash
cd EmulationModeling/10_neural_network_from_scratch
python main.py
```

## 🧱 Architecture

The default network is:
```
2 → 16 → 16 → 1
```

You can change layer sizes or activation choices by editing `main.py`.
