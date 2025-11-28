"""MNIST handwritten digit classifier using a Convolutional Neural Network.

This module implements a simple CNN architecture for classifying MNIST digits.
Uses PyTorch with Conv2d layers, max pooling, and fully connected layers.

Usage:
    python mnist_cnn.py --epochs 5 --batch-size 64
"""

import argparse
from typing import Tuple

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


def build_dataloaders(
    batch_size: int, use_subset: bool, subset_size: int
) -> Tuple[DataLoader, DataLoader]:
    """Create training and test data loaders for MNIST.

    Args:
        batch_size: Number of samples per batch.
        use_subset: If True, use only a subset of training data.
        subset_size: Number of training samples when subset is enabled.

    Returns:
        Tuple of (train_loader, test_loader).
    """
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
        ]
    )

    train_dataset = datasets.MNIST(
        root="./data", train=True, download=True, transform=transform
    )
    test_dataset = datasets.MNIST(
        root="./data", train=False, download=True, transform=transform
    )

    if use_subset:
        subset_indices = list(range(min(subset_size, len(train_dataset))))
        train_dataset = Subset(train_dataset, subset_indices)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader


class MnistCNN(nn.Module):
    """Simple CNN for MNIST digit classification."""

    def __init__(self) -> None:
        """Initialize the CNN architecture."""
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.pool = nn.MaxPool2d(2)
        self.dropout = nn.Dropout(0.25)
        self.fc1 = nn.Linear(64 * 5 * 5, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network."""
        x = torch.relu(self.conv1(x))
        x = self.pool(torch.relu(self.conv2(x)))
        x = self.dropout(x)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    """Train the model for one epoch.

    Returns:
        float: Average training loss for the epoch.
    """
    model.train()
    running_loss = 0.0
    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

    return running_loss / len(dataloader.dataset)


def evaluate(
    model: nn.Module, dataloader: DataLoader, device: torch.device
) -> Tuple[float, float]:
    """Evaluate model accuracy and loss on a dataset.

    Returns:
        Tuple of (average_loss, accuracy_percentage).
    """
    model.eval()
    correct = 0
    total = 0
    loss_sum = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss_sum += loss.item() * images.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    avg_loss = loss_sum / total
    accuracy = 100 * correct / total
    return avg_loss, accuracy


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Train a CNN on MNIST")
    parser.add_argument(
        "--epochs", type=int, default=1, help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size", type=int, default=64, help="Batch size for data loaders"
    )
    parser.add_argument(
        "--subset",
        action="store_true",
        help="Use a small subset of the training data for quick experiments",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=5_000,
        help="Number of training samples to use when subset is enabled",
    )
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    return parser.parse_args()


def main() -> None:
    """Main training loop."""
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_loader, test_loader = build_dataloaders(
        args.batch_size, args.subset, args.subset_size
    )
    model = MnistCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)

    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        test_loss, test_accuracy = evaluate(model, test_loader, device)
        print(
            f"Epoch {epoch}/{args.epochs} - "
            f"Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}, Test Accuracy: {test_accuracy:.2f}%"
        )

    _, final_accuracy = evaluate(model, test_loader, device)
    print(f"Final Test Accuracy: {final_accuracy:.2f}%")


if __name__ == "__main__":
    main()
