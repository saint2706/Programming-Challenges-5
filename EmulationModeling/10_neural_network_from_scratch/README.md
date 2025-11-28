# Neural Network From Scratch

A pure NumPy implementation of a feedforward neural network with backpropagation and training visualization.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)

## 🧠 Theory

### Feedforward Neural Network

A network where information flows forward from input to output:

```
Input → Hidden Layer(s) → Output
```

### Forward Pass

Compute output by passing data through layers:

```
z = W·x + b    (linear transformation)
a = σ(z)       (activation function)
```

### Backpropagation

Learn by computing gradients via chain rule:

1. **Forward pass**: Compute predictions
2. **Compute loss**: Measure error
3. **Backward pass**: Compute ∂Loss/∂W for each layer
4. **Update weights**: W ← W - α·∂Loss/∂W

### Activation Functions

- **ReLU**: f(x) = max(0, x) - Fast, effective
- **Sigmoid**: f(x) = 1/(1+e⁻ˣ) - For output probabilities
- **Tanh**: f(x) = tanh(x) - Centered at zero

## 💻 Installation

Requires Python 3.8+ with NumPy and Matplotlib:

```bash
pip install numpy matplotlib
```

## 🚀 Usage

### Training a Network

```bash
cd EmulationModeling/10_neural_network_from_scratch
python main.py
```

The default configuration trains on synthetic data and displays:

- Loss curve over training
- Decision boundaries (for 2D data)
- Final accuracy

### Custom Architecture

Edit `main.py` to configure:

```python
# Network with 2 hidden layers
nn = NeuralNetwork([input_size, 64, 32, output_size])

# Training parameters
nn.train(X_train, y_train, epochs=1000, learning_rate=0.01)
```

## 🏗 Architecture

### Layer Types

#### Dense (Fully Connected)

Every neuron connects to all neurons in previous layer

```python
output = activation(weights @ input + bias)
```

### Loss Functions

#### Mean Squared Error (MSE)

For regression:

```
MSE = (1/n) Σ(y_pred - y_true)²
```

#### Cross-Entropy

For classification:

```
CE = -Σ y_true·log(y_pred)
```

### Optimization

#### Gradient Descent

Basic weight update rule:

```
W_new = W_old - learning_rate * gradient
```

#### Mini-batch Training

- Process data in small batches
- Faster convergence
- Better generalization

## 📊 Visualization

The implementation includes:

- **Loss Plot**: Training loss vs. epoch
- **Decision Boundaries**: For 2D classification problems
- **Weight Histograms**: Distribution of learned weights
- **Activation Distributions**: Layer outputs during training

## ✨ Features

- Pure NumPy implementation (educational)
- Modular layer design
- Multiple activation functions
- Configurable architecture
- Training visualization
- Support for regression and classification
- Mini-batch gradient descent
- Weight initialization strategies
