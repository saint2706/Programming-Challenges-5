from __future__ import annotations

import torch

from ArtificialIntelligence.style_transfer import (
    StyleTransferConfig,
    compute_content_loss,
    compute_style_loss,
    gram_matrix,
)


def test_gram_matrix_normalizes_by_dimensions() -> None:
    feature_map = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]], [[1.0, 1.0], [1.0, 1.0]]]])
    gram = gram_matrix(feature_map)

    expected = torch.tensor(
        [
            [30.0, 10.0],
            [10.0, 4.0],
        ]
    ) / (2 * 2 * 2)
    assert torch.allclose(gram, expected)


def test_style_loss_respects_layer_weights() -> None:
    generated_features = {
        "conv1_1": torch.tensor([[[[1.0, 1.0], [1.0, 1.0]]]]),
        "conv2_1": torch.tensor([[[[0.0, 1.0], [2.0, 3.0]]]]),
    }

    style_features = {
        "conv1_1": torch.tensor([[[[1.0, 1.0], [1.0, 1.0]]]]),
        "conv2_1": torch.tensor([[[[3.0, 2.0], [1.0, 0.0]]]]),
    }
    style_grams = {key: gram_matrix(tensor) for key, tensor in style_features.items()}

    weights = {"conv1_1": 0.5, "conv2_1": 2.0}
    loss = compute_style_loss(generated_features, style_grams, weights)

    expected_loss = sum(
        weights[layer]
        * torch.nn.functional.mse_loss(
            gram_matrix(generated_features[layer]), style_grams[layer]
        )
        for layer in weights
    )
    assert torch.allclose(loss, expected_loss)


def test_content_loss_averages_across_layers() -> None:
    config = StyleTransferConfig(content_layers=("conv3_1", "conv4_2"))

    content_features = {
        "conv3_1": torch.tensor([[[[1.0]]]]),
        "conv4_2": torch.tensor([[[[2.0]]]]),
    }
    generated_features = {
        "conv3_1": torch.tensor([[[[0.0]]]]),
        "conv4_2": torch.tensor([[[[4.0]]]]),
    }

    loss = compute_content_loss(
        generated_features=generated_features,
        content_features=content_features,
        content_layers=config.content_layers,
    )

    loss_conv3 = torch.nn.functional.mse_loss(
        generated_features["conv3_1"], content_features["conv3_1"]
    )
    loss_conv4 = torch.nn.functional.mse_loss(
        generated_features["conv4_2"], content_features["conv4_2"]
    )

    assert torch.allclose(loss, (loss_conv3 + loss_conv4) / 2)
