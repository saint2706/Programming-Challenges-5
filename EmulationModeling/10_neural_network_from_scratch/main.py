import matplotlib.pyplot as plt
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

    # Visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Loss Curve
    ax1.plot(losses)
    ax1.set_title("Training Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("MSE Loss")

    # Decision Boundary
    ax2.set_title("Decision Boundary")

    # Grid for contour plot
    xx, yy = np.meshgrid(np.linspace(-1.2, 1.2, 50), np.linspace(-1.2, 1.2, 50))
    grid = np.c_[xx.ravel(), yy.ravel()]

    preds_grid = net.forward(grid).reshape(xx.shape)

    ax2.contourf(xx, yy, preds_grid, levels=20, cmap="RdBu_r", alpha=0.6)

    # Scatter points
    ax2.scatter(
        X[y.flatten() == 0, 0], X[y.flatten() == 0, 1], c="blue", label="Class 0"
    )
    ax2.scatter(
        X[y.flatten() == 1, 0], X[y.flatten() == 1, 1], c="red", label="Class 1"
    )
    ax2.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
