from __future__ import annotations

from typing import Sequence

import torch
from PIL import Image

from ArtificialIntelligence.auto_image_tagger import AutoImageTagger, LabelPrediction


class DummyModel(torch.nn.Module):
    """Simple model that always returns the same logits for testing."""

    def __init__(self, logits: torch.Tensor) -> None:
        super().__init__()
        self.register_buffer("logits", logits)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        batch_size = inputs.shape[0]
        if self.logits.ndim == 1:
            return self.logits.unsqueeze(0).expand(batch_size, -1)
        return self.logits.expand(batch_size, -1)


def _constant_preprocess(_: Image.Image) -> torch.Tensor:
    """Return a minimal tensor so the dummy model receives input."""

    return torch.ones((3, 2, 2))


def test_predict_orders_labels_by_probability() -> None:
    logits = torch.tensor([1.0, 3.0, 2.0])
    categories: Sequence[str] = ["cat", "dog", "bird"]
    model = DummyModel(logits)
    tagger = AutoImageTagger(
        model=model,
        preprocess=_constant_preprocess,
        categories=categories,
        device="cpu",
    )

    image = Image.new("RGB", (2, 2))
    predictions = tagger.predict(image, top_k=2)

    assert predictions == [
        LabelPrediction(label="dog", score=predictions[0].score),
        LabelPrediction(label="bird", score=predictions[1].score),
    ]
    assert predictions[0].score > predictions[1].score


def test_extract_predictions_limits_top_k_to_available_classes() -> None:
    logits = torch.tensor([[2.5, 0.1]])
    categories: Sequence[str] = ["oak", "pine"]
    model = DummyModel(logits)
    tagger = AutoImageTagger(
        model=model,
        preprocess=_constant_preprocess,
        categories=categories,
        device="cpu",
    )

    image = Image.new("RGB", (2, 2))
    predictions = tagger.predict(image, top_k=5)

    assert len(predictions) == 2
    assert predictions[0].label == "oak"
    assert all(isinstance(pred, LabelPrediction) for pred in predictions)
