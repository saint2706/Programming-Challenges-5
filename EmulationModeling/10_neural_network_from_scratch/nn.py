"""Neural network layers and components built from scratch with NumPy.

This module provides simple implementations of common neural network
building blocks including linear layers, activation functions, and loss
functions. Designed for educational purposes to understand backpropagation
and gradient descent.
"""
import numpy as np


class Linear:
    """Fully connected (dense) layer with learnable weights and bias."""

    def __init__(self, input_dim, output_dim):
        """Initialize the linear layer with Xavier initialization.

        Args:
            input_dim: Number of input features.
            output_dim: Number of output features.
        """
        # Xavier initialization
        self.weights = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)
        self.bias = np.zeros(output_dim)
        self.input = None
        self.dw = None
        self.db = None

    def forward(self, x):
        """Compute the forward pass: output = x @ W + b."""
        self.input = x
        return np.dot(x, self.weights) + self.bias

    def backward(self, grad_output, learning_rate):
        """Compute gradients and update weights using SGD."""
        # grad_output: (batch_size, output_dim)
        # input: (batch_size, input_dim)

        # dw: (input_dim, output_dim)
        self.dw = np.dot(self.input.T, grad_output)
        self.db = np.sum(grad_output, axis=0)

        grad_input = np.dot(grad_output, self.weights.T)

        # Update parameters (SGD)
        self.weights -= learning_rate * self.dw
        self.bias -= learning_rate * self.db

        return grad_input

class ReLU:
    """Rectified Linear Unit activation function."""

    def __init__(self):
        """
        Docstring for __init__.
        """
        self.input = None

    def forward(self, x):
        """Apply ReLU: max(0, x)."""
        self.input = x
        return np.maximum(0, x)

    def backward(self, grad_output, learning_rate):
        """Gradient is passed through where input > 0."""
        return grad_output * (self.input > 0)


class Sigmoid:
    """Sigmoid activation function."""

    def __init__(self):
        """
        Docstring for __init__.
        """
        self.output = None

    def forward(self, x):
        """Apply sigmoid: 1 / (1 + exp(-x))."""
        self.output = 1 / (1 + np.exp(-x))
        return self.output

    def backward(self, grad_output, learning_rate):
        """Gradient: sigmoid(x) * (1 - sigmoid(x))."""
        return grad_output * self.output * (1 - self.output)


class MSELoss:
    """Mean Squared Error loss function."""

    def forward(self, predictions, targets):
        """Compute MSE loss."""
        return np.mean((predictions - targets) ** 2)

    def backward(self, predictions, targets):
        """Compute gradient of MSE loss."""
        return 2 * (predictions - targets) / predictions.shape[0]


class NeuralNetwork:
    """Container for stacking layers into a sequential network."""

    def __init__(self):
        """
        Docstring for __init__.
        """
        self.layers = []

    def add(self, layer):
        """Add a layer to the network."""
        self.layers.append(layer)

    def forward(self, x):
        """Forward pass through all layers."""
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, grad, learning_rate):
        """Backward pass through all layers in reverse order."""
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)
