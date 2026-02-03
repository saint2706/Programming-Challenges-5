import numpy as np
from nn import Linear, MSELoss, NeuralNetwork, ReLU, Sigmoid


def generate_data(n_samples=200):
    # Generate concentric circles
    # Class 0: inner circle
    # Class 1: outer ring

    X = []
    y = []

    for _ in range(n_samples // 2):
        # Inner
        r = np.random.uniform(0, 0.5)
        angle = np.random.uniform(0, 2 * np.pi)
        X.append([r * np.cos(angle), r * np.sin(angle)])
        y.append([0])

        # Outer
        r = np.random.uniform(0.7, 1.0)
        angle = np.random.uniform(0, 2 * np.pi)
        X.append([r * np.cos(angle), r * np.sin(angle)])
        y.append([1])

    return np.array(X), np.array(y)


def main():
    X, y = generate_data()

    # Model: 2 -> 16 -> 16 -> 1
    net = NeuralNetwork()
    net.add(Linear(2, 16))
    net.add(ReLU())
    net.add(Linear(16, 16))
    net.add(ReLU())
    net.add(Linear(16, 1))
    net.add(Sigmoid())  # Binary classification

    loss_fn = MSELoss()

    epochs = 1000
    lr = 0.01
    losses = []

    print(f"Training for {epochs} epochs...")

    for i in range(epochs):
        # Forward
        preds = net.forward(X)
        loss = loss_fn.forward(preds, y)
        losses.append(loss)

        # Backward
        grad = loss_fn.backward(preds, y)
        net.backward(grad, lr)

        if i % 100 == 0:
            print(f"Epoch {i}, Loss: {loss:.4f}")

    print(f"Final Loss: {loss:.4f}")

    print(f"Tracked {len(losses)} loss values for diagnostics.")


if __name__ == "__main__":
    main()
