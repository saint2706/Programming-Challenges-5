from __future__ import annotations

from pathlib import Path

from ArtificialIntelligence.nn_visual_debugger import TrainingConfig, run_debug_session


def test_heatmap_and_tensorboard_artifacts(tmp_path: Path) -> None:
    """Ensure a debug run writes heatmaps and TensorBoard event files."""

    config = TrainingConfig(
        batch_size=8,
        epochs=1,
        learning_rate=0.01,
        log_dir=tmp_path / "nn_logs",
        use_fake_data=True,
        dataset_size=32,
    )

    result = run_debug_session(config)

    heatmaps = list((config.log_dir / "heatmaps").glob("*.png"))
    weight_maps = [path for path in heatmaps if "weights" in path.name]
    activation_maps = [path for path in heatmaps if "activations" in path.name]

    assert heatmaps, "No heatmaps were generated during the debug session."
    assert weight_maps, "Weight heatmaps were not saved."
    assert activation_maps, "Activation heatmaps were not saved."

    for path in weight_maps + activation_maps:
        assert path.exists() and path.stat().st_size > 0

    assert result.event_files, "TensorBoard event files were not written."
    for event_file in result.event_files:
        assert event_file.exists()
