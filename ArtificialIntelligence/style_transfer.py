"""Neural style transfer implementation using VGG19.

The module provides utilities to load content/style images, optimize a generated
image with combined content and style losses, and save the stylized output.

Example:
    python ArtificialIntelligence/style_transfer.py \
        --content path/to/content.jpg \
        --style path/to/style.jpg \
        --output stylized.png
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Sequence

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms
from torchvision.models import VGG19_Weights


MEAN = torch.tensor([0.485, 0.456, 0.406])
STD = torch.tensor([0.229, 0.224, 0.225])


@dataclass
class StyleTransferConfig:
    """Configuration for the style transfer optimization loop."""

    max_size: int = 512
    steps: int = 200
    style_weight: float = 1e2
    content_weight: float = 1e4
    total_variation_weight: float = 1e-5
    style_layer_weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "conv1_1": 0.2,
            "conv2_1": 0.2,
            "conv3_1": 0.2,
            "conv4_1": 0.2,
            "conv5_1": 0.2,
        }
    )
    content_layers: Sequence[str] = field(default_factory=lambda: ("conv4_2",))


_LAYER_MAP = {0: "conv1_1", 5: "conv2_1", 10: "conv3_1", 19: "conv4_1", 21: "conv4_2", 28: "conv5_1"}


def gram_matrix(feature_map: torch.Tensor) -> torch.Tensor:
    """Compute the normalized Gram matrix for a feature map.

    Args:
        feature_map: Tensor of shape (batch, channels, height, width).

    Returns:
        Normalized Gram matrix of shape (channels, channels).
    """

    _, channels, height, width = feature_map.shape
    features = feature_map.view(channels, height * width)
    gram = features @ features.t()
    return gram / (channels * height * width)


def get_feature_maps(image: torch.Tensor, model: torch.nn.Module) -> Dict[str, torch.Tensor]:
    """Collect feature maps from selected VGG layers.

    Args:
        image: Input image tensor of shape (1, 3, H, W) normalized for VGG.
        model: Pretrained VGG feature extractor.

    Returns:
        Mapping from layer names to their feature maps.
    """

    features: Dict[str, torch.Tensor] = {}
    output = image
    for index, layer in enumerate(model):
        output = layer(output)
        if index in _LAYER_MAP:
            features[_LAYER_MAP[index]] = output
    return features


def compute_content_loss(
    generated_features: Mapping[str, torch.Tensor],
    content_features: Mapping[str, torch.Tensor],
    content_layers: Sequence[str],
) -> torch.Tensor:
    """Compute average content loss over the specified layers."""

    losses = [
        F.mse_loss(generated_features[layer], content_features[layer])
        for layer in content_layers
    ]
    return sum(losses) / len(losses)


def compute_style_loss(
    generated_features: Mapping[str, torch.Tensor],
    style_grams: Mapping[str, torch.Tensor],
    style_layer_weights: Mapping[str, float],
) -> torch.Tensor:
    """Compute weighted style loss using Gram matrices."""

    device = next(iter(generated_features.values())).device
    loss = torch.tensor(0.0, device=device)
    for layer, weight in style_layer_weights.items():
        generated_gram = gram_matrix(generated_features[layer])
        loss = loss + weight * F.mse_loss(generated_gram, style_grams[layer])
    return loss


def total_variation_loss(image: torch.Tensor) -> torch.Tensor:
    """Encourage smoothness in the generated image."""

    x_diff = torch.sum(torch.abs(image[:, :, :, :-1] - image[:, :, :, 1:]))
    y_diff = torch.sum(torch.abs(image[:, :, :-1, :] - image[:, :, 1:, :]))
    return x_diff + y_diff


def load_image(image_path: str | Path, max_size: int, device: torch.device) -> torch.Tensor:
    """Load and normalize an image for VGG."""

    image = Image.open(image_path).convert("RGB")
    largest_side = max(image.size)
    if largest_side > max_size:
        scale = max_size / float(largest_side)
        new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
        image = image.resize(new_size, Image.LANCZOS)

    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ]
    )
    tensor = transform(image).unsqueeze(0)
    return tensor.to(device)


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    """Convert a normalized tensor back to a PIL Image."""

    image = tensor.detach().cpu().clone().squeeze(0)
    image = image * STD[:, None, None] + MEAN[:, None, None]
    image = torch.clamp(image, 0, 1)
    to_pil = transforms.ToPILImage()
    return to_pil(image)


def _build_vgg19(device: torch.device) -> torch.nn.Module:
    """Load and freeze the VGG19 feature extractor."""

    vgg = models.vgg19(weights=VGG19_Weights.DEFAULT).features.to(device).eval()
    for parameter in vgg.parameters():
        parameter.requires_grad_(False)
    return vgg


def run_style_transfer(
    content_image_path: str | Path,
    style_image_path: str | Path,
    output_image_path: str | Path,
    config: StyleTransferConfig | None = None,
    device: torch.device | None = None,
) -> Path:
    """Run the neural style transfer optimization loop.

    Args:
        content_image_path: Path to the content image.
        style_image_path: Path to the style reference image.
        output_image_path: Where to save the stylized image.
        config: Optional configuration object.
        device: Optional torch device override.

    Returns:
        Path to the saved stylized image.
    """

    cfg = config or StyleTransferConfig()
    torch_device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

    content_image = load_image(content_image_path, cfg.max_size, torch_device)
    style_image = load_image(style_image_path, cfg.max_size, torch_device)

    vgg = _build_vgg19(torch_device)

    content_features = get_feature_maps(content_image, vgg)
    style_features = get_feature_maps(style_image, vgg)
    style_grams = {layer: gram_matrix(style_features[layer]) for layer in cfg.style_layer_weights}

    generated = content_image.clone().requires_grad_(True)
    optimizer = torch.optim.Adam([generated], lr=0.02)

    for step in range(cfg.steps):
        optimizer.zero_grad()
        generated_features = get_feature_maps(generated, vgg)
        content_loss = compute_content_loss(
            generated_features,
            content_features,
            cfg.content_layers,
        )
        style_loss = compute_style_loss(
            generated_features,
            style_grams,
            cfg.style_layer_weights,
        )
        tv_loss = total_variation_loss(generated)

        total_loss = (
            cfg.content_weight * content_loss
            + cfg.style_weight * style_loss
            + cfg.total_variation_weight * tv_loss
        )
        total_loss.backward()
        optimizer.step()
        generated.data.clamp_(min=-3.0, max=3.0)

    output_image = tensor_to_image(generated)
    output_path = Path(output_image_path)
    output_image.save(output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Neural style transfer with VGG19")
    parser.add_argument("--content", required=True, help="Path to the content image")
    parser.add_argument("--style", required=True, help="Path to the style reference image")
    parser.add_argument("--output", required=True, help="Path to save the stylized result")
    parser.add_argument("--steps", type=int, default=200, help="Number of optimization steps")
    parser.add_argument(
        "--max-size",
        type=int,
        default=512,
        help="Maximum size for the longer image dimension",
    )
    parser.add_argument(
        "--content-weight",
        type=float,
        default=1e4,
        help="Weight for the content loss component",
    )
    parser.add_argument(
        "--style-weight",
        type=float,
        default=1e2,
        help="Weight for the style loss component",
    )
    parser.add_argument(
        "--tv-weight",
        type=float,
        default=1e-5,
        help="Weight for the total variation regularizer",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""

    args = parse_args()
    config = StyleTransferConfig(
        max_size=args.max_size,
        steps=args.steps,
        style_weight=args.style_weight,
        content_weight=args.content_weight,
        total_variation_weight=args.tv_weight,
    )
    run_style_transfer(
        content_image_path=args.content,
        style_image_path=args.style,
        output_image_path=args.output,
        config=config,
    )


if __name__ == "__main__":
    main()
