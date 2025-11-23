import numpy as np

class Linear:
    def __init__(self, input_dim, output_dim):
        # Xavier initialization
        self.weights = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)
        self.bias = np.zeros(output_dim)
        self.input = None
        self.dw = None
        self.db = None

    def forward(self, x):
        self.input = x
        return np.dot(x, self.weights) + self.bias

    def backward(self, grad_output, learning_rate):
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
    def __init__(self):
        self.input = None

    def forward(self, x):
        self.input = x
        return np.maximum(0, x)

    def backward(self, grad_output, learning_rate):
        return grad_output * (self.input > 0)

class Sigmoid:
    def __init__(self):
        self.output = None

    def forward(self, x):
        self.output = 1 / (1 + np.exp(-x))
        return self.output

    def backward(self, grad_output, learning_rate):
        return grad_output * self.output * (1 - self.output)

class MSELoss:
    def forward(self, predictions, targets):
        return np.mean((predictions - targets) ** 2)

    def backward(self, predictions, targets):
        return 2 * (predictions - targets) / predictions.shape[0]

class NeuralNetwork:
    def __init__(self):
        self.layers = []

    def add(self, layer):
        self.layers.append(layer)

    def forward(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, grad, learning_rate):
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)
