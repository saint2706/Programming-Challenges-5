from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from torch import Tensor, nn, optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms


@dataclass
class TrainingConfig:
    """Configuration for running a visual debugging session."""

    batch_size: int = 64
    epochs: int = 3
    learning_rate: float = 0.01
    momentum: float = 0.9
    log_dir: Path = Path("runs/nn_visual_debugger")
    data_dir: Path = Path("data")
    use_fake_data: bool = False
    dataset_size: int | None = None


@dataclass
class SessionResult:
    """Artifacts produced by a run."""

    log_dir: Path
    heatmap_paths: List[Path]
    event_files: List[Path]


class SmallCNN(nn.Module):
    """Simple CNN suitable for MNIST-sized images."""

    def __init__(self) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(1, 8, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(8, 16, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(16 * 14 * 14, 64)
        self.fc2 = nn.Linear(64, 10)

    def forward(self, x: Tensor) -> Tensor:
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        return self.fc2(x)


def prepare_dataloader(config: TrainingConfig) -> DataLoader:
    """Prepare MNIST (or fake) dataloader.

    Args:
        config: Settings for the current run.

    Returns:
        A DataLoader with either MNIST or synthetic samples.
    """

    transform = transforms.Compose([transforms.ToTensor()])

    if config.use_fake_data:
        dataset_size = config.dataset_size or 256
        dataset = datasets.FakeData(
            size=dataset_size,
            image_size=(1, 28, 28),
            num_classes=10,
            transform=transform,
        )
    else:
        dataset = datasets.MNIST(
            root=str(config.data_dir), train=True, download=True, transform=transform
        )

    return DataLoader(dataset, batch_size=config.batch_size, shuffle=True)


def register_activation_hooks(model: nn.Module) -> Tuple[Dict[str, Tensor], List[torch.utils.hooks.RemovableHandle]]:
    """Attach hooks to store first batch activations for each target layer.

    Args:
        model: The network to instrument.

    Returns:
        A tuple containing the activation store and the removable hook handles.
    """

    activations: Dict[str, Tensor] = {}
    handles: List[torch.utils.hooks.RemovableHandle] = []

    def _make_hook(name: str):
        def hook(_: nn.Module, __: Tensor, output: Tensor) -> None:
            if name not in activations:
                activations[name] = output.detach().cpu()

        return hook

    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            handles.append(module.register_forward_hook(_make_hook(name)))

    return activations, handles


def _reshape_weight(weight: Tensor) -> np.ndarray:
    """Flatten convolutional kernels or linear weights for visualization."""

    if weight.dim() == 4:
        return weight.view(weight.shape[0], -1).numpy()
    if weight.dim() == 2:
        return weight.numpy()
    return weight.view(1, -1).numpy()


def _activation_matrix(activation: Tensor) -> np.ndarray:
    """Convert activation tensors into 2D matrices for plotting."""

    if activation.dim() == 4:
        sample = activation[0]
        return sample.view(sample.shape[0], -1).numpy()
    sample = activation[0]
    return sample.view(1, -1).numpy()


def _figure_to_image(fig: plt.Figure) -> Tensor:
    """Transform a matplotlib figure into a TensorBoard-ready image tensor."""

    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    raw = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    data = raw.reshape(height, width, 4)[..., :3]
    array = np.transpose(data, (2, 0, 1))
    return torch.tensor(array, dtype=torch.float32) / 255.0


def save_heatmap(
    matrix: np.ndarray,
    path: Path,
    title: str,
    writer: SummaryWriter | None = None,
    tag: str | None = None,
    epoch: int | None = None,
) -> None:
    """Persist a heatmap to disk and optionally to TensorBoard.

    Args:
        matrix: 2D array to visualize.
        path: Destination for the PNG file.
        title: Plot title.
        writer: Optional SummaryWriter for TensorBoard images.
        tag: TensorBoard image tag.
        epoch: Current epoch, used as the TensorBoard step.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    sns.heatmap(matrix, cmap="viridis")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path)
    fig = plt.gcf()
    if writer is not None and tag is not None and epoch is not None:
        image = _figure_to_image(fig)
        writer.add_image(tag, image, global_step=epoch)
    plt.close(fig)


def log_epoch_artifacts(
    *,
    epoch: int,
    model: nn.Module,
    activations: Dict[str, Tensor],
    heatmap_dir: Path,
    writer: SummaryWriter,
) -> List[Path]:
    """Save weight and activation heatmaps and push TensorBoard summaries.

    Args:
        epoch: Current epoch number (1-indexed).
        model: The trained network.
        activations: Stored activation tensors keyed by layer name.
        heatmap_dir: Directory in which to save PNGs.
        writer: Active TensorBoard writer.

    Returns:
        List of generated heatmap file paths.
    """

    generated: List[Path] = []
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            weight_matrix = _reshape_weight(module.weight.detach().cpu())
            weight_path = heatmap_dir / f"{name}_weights_epoch_{epoch}.png"
            save_heatmap(
                weight_matrix,
                weight_path,
                f"{name} weights (epoch {epoch})",
                writer=writer,
                tag=f"weights/{name}",
                epoch=epoch,
            )
            writer.add_histogram(f"weights_hist/{name}", module.weight, epoch)
            generated.append(weight_path)

            if name in activations:
                act_matrix = _activation_matrix(activations[name])
                act_path = heatmap_dir / f"{name}_activations_epoch_{epoch}.png"
                save_heatmap(
                    act_matrix,
                    act_path,
                    f"{name} activations (epoch {epoch})",
                    writer=writer,
                    tag=f"activations/{name}",
                    epoch=epoch,
                )
                generated.append(act_path)

    return generated


def train_model(config: TrainingConfig) -> SessionResult:
    """Train the model while logging weights and activations.

    Args:
        config: Run configuration.

    Returns:
        SessionResult containing paths to generated artifacts.
    """

    torch.manual_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if config.log_dir.exists():
        shutil.rmtree(config.log_dir)
    config.log_dir.mkdir(parents=True, exist_ok=True)

    dataloader = prepare_dataloader(config)
    model = SmallCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=config.learning_rate, momentum=config.momentum)
    writer = SummaryWriter(log_dir=str(config.log_dir))
    activation_store, handles = register_activation_hooks(model)
    heatmap_dir = config.log_dir / "heatmaps"

    generated_paths: List[Path] = []

    for epoch in range(1, config.epochs + 1):
        model.train()
        running_loss = 0.0
        total_examples = 0
        correct = 0
        activation_store.clear()

        for images, targets in dataloader:
            images, targets = images.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total_examples += targets.numel()

        avg_loss = running_loss / max(total_examples, 1)
        accuracy = correct / max(total_examples, 1)
        writer.add_scalar("train/loss", avg_loss, epoch)
        writer.add_scalar("train/accuracy", accuracy, epoch)
        generated_paths.extend(
            log_epoch_artifacts(
                epoch=epoch,
                model=model,
                activations=activation_store,
                heatmap_dir=heatmap_dir,
                writer=writer,
            )
        )

    for handle in handles:
        handle.remove()
    writer.flush()
    writer.close()

    event_files = list(config.log_dir.glob("events.*"))

    return SessionResult(log_dir=config.log_dir, heatmap_paths=generated_paths, event_files=event_files)


def parse_args() -> TrainingConfig:
    """Parse CLI arguments into a TrainingConfig."""

    parser = argparse.ArgumentParser(description="Train a small CNN and log debug visuals.")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs to train")
    parser.add_argument("--learning-rate", type=float, default=0.01, help="Optimizer learning rate")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--log-dir", type=Path, default=Path("runs/nn_visual_debugger"), help="Directory for TensorBoard logs and heatmaps")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Directory for MNIST data downloads")
    parser.add_argument(
        "--use-fake-data",
        action="store_true",
        help="Use synthetic data instead of downloading MNIST (helps in offline environments)",
    )
    parser.add_argument("--dataset-size", type=int, default=None, help="Limit dataset size (only for fake data)")
    args = parser.parse_args()

    return TrainingConfig(
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        momentum=args.momentum,
        log_dir=args.log_dir,
        data_dir=args.data_dir,
        use_fake_data=args.use_fake_data,
        dataset_size=args.dataset_size,
    )


def run_debug_session(config: TrainingConfig | None = None) -> SessionResult:
    """Convenience wrapper for tests and scripts.

    Args:
        config: Optional override configuration.

    Returns:
        SessionResult populated with run artifacts.
    """

    return train_model(config or TrainingConfig())


if __name__ == "__main__":
    config = parse_args()
    result = train_model(config)
    print(f"TensorBoard logs written to: {result.log_dir}")
    print("Example command to inspect logs:")
    print(f"tensorboard --logdir {result.log_dir}")
