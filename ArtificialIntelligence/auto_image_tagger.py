"""
Artificial Intelligence project implementation.
"""

from __future__ import annotations

import argparse
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Sequence
from urllib.parse import urlparse

import requests
import torch
from PIL import Image
from torchvision import models
from torchvision.models import ResNet50_Weights


@dataclass
class LabelPrediction:
    """Prediction tuple for an image classification result."""

    label: str
    score: float


class AutoImageTagger:
    """Run image tagging using a pre-trained classifier."""

    def __init__(
        self,
        *,
        model: torch.nn.Module | None = None,
        preprocess: Callable[[Image.Image], torch.Tensor] | None = None,
        categories: Sequence[str] | None = None,
        device: str | None = None,
        weights: ResNet50_Weights | None = None,
    ) -> None:
        """Initialize the tagger with optional pre-loaded components.

        Args:
            model: Torch model to run for inference. Defaults to ResNet50.
            preprocess: Transform pipeline applied before inference.
            categories: Ordered labels that align with the model output.
            device: Torch device string such as "cpu" or "cuda".
            weights: Torchvision weights used to create the default model.
        """

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if model is None or preprocess is None or categories is None:
            weights = weights or ResNet50_Weights.IMAGENET1K_V2
            model = model or models.resnet50(weights=weights)
            preprocess = preprocess or weights.transforms()
            categories = categories or weights.meta["categories"]

        self.model = model.to(self.device).eval()
        self.preprocess = preprocess
        self.categories = list(categories)

    def load_image(self, source: str) -> Image.Image:
        """Load an image from a local path or URL.

        Args:
            source: Path or HTTP(S) URL for the image.

        Returns:
            RGB Pillow image ready for preprocessing.
        """

        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            data = io.BytesIO(response.content)
            image = Image.open(data)
        else:
            image = Image.open(Path(source).expanduser())
        return image.convert("RGB")

    def _extract_predictions(self, logits: torch.Tensor, top_k: int) -> List[LabelPrediction]:
        """Convert model logits into sorted predictions.

        Args:
            logits: Raw model outputs of shape (batch, num_classes) or (num_classes,).
            top_k: Number of predictions to return.

        Returns:
            Ordered list of label predictions, highest score first.
        """

        if logits.ndim == 1:
            logits = logits.unsqueeze(0)

        probabilities = torch.nn.functional.softmax(logits, dim=1)
        k = min(top_k, probabilities.shape[1])
        scores, indices = probabilities.topk(k, dim=1)
        categories = self.categories

        return [
            LabelPrediction(label=categories[int(index)], score=float(score))
            for score, index in zip(scores[0], indices[0])
        ]

    def predict(self, image: Image.Image, top_k: int = 5) -> List[LabelPrediction]:
        """Run inference on a single image and return top labels."""

        tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
        return self._extract_predictions(logits, top_k)


def _format_predictions(predictions: Iterable[LabelPrediction]) -> str:
    """Render predictions as indented lines for CLI output."""

    return "\n".join(
        f"    {pred.label}: {pred.score:.3f}" for pred in predictions
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Auto-tag images with ResNet50")
    parser.add_argument(
        "images",
        nargs="+",
        help="Local file paths or HTTP(S) URLs to classify.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of labels to print for each image (default: 5)",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default=None,
        help="Force running on CPU or CUDA. Defaults to auto-detection.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the CLI runner."""

    args = parse_args(argv)
    tagger = AutoImageTagger(device=args.device)

    for image_path in args.images:
        image = tagger.load_image(image_path)
        predictions = tagger.predict(image, top_k=args.top_k)
        print(image_path)
        print(_format_predictions(predictions))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
