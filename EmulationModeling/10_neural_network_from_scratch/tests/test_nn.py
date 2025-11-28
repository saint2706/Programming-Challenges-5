"""
Emulation/Modeling project implementation.
"""

import unittest
import numpy as np
from nn import NeuralNetwork, Linear, ReLU, MSELoss

class TestNN(unittest.TestCase):
    """
    Docstring for TestNN.
    """
    def test_linear_shape(self):
        """
        Docstring for test_linear_shape.
        """
        layer = Linear(2, 3)
        x = np.random.randn(5, 2) # Batch 5
        out = layer.forward(x)
        self.assertEqual(out.shape, (5, 3))

    def test_relu(self):
        """
        Docstring for test_relu.
        """
        layer = ReLU()
        x = np.array([[-1, 1], [0, 2]])
        out = layer.forward(x)
        expected = np.array([[0, 1], [0, 2]])
        np.testing.assert_array_equal(out, expected)

    def test_overfitting_simple_func(self):
        # Learn y = 2x
        """
        Docstring for test_overfitting_simple_func.
        """
        X = np.array([[1], [2], [3], [4]])
        y = np.array([[2], [4], [6], [8]])

        net = NeuralNetwork()
        net.add(Linear(1, 1))
        # No activation needed for linear regression

        loss_fn = MSELoss()
        lr = 0.01

        for _ in range(500):
            pred = net.forward(X)
            grad = loss_fn.backward(pred, y)
            net.backward(grad, lr)

        final_loss = loss_fn.forward(net.forward(X), y)
        self.assertLess(final_loss, 0.1)

if __name__ == '__main__':
    unittest.main()
