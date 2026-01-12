"""Tests for the toy seq2seq neural machine translation model."""

from __future__ import annotations

import torch

from ArtificialIntelligence.toy_nmt_seq2seq import (
    Decoder,
    Encoder,
    Seq2Seq,
    create_dataloaders,
    train,
)


def test_forward_shapes() -> None:
    loader, vocab_src, vocab_tgt = create_dataloaders(batch_size=2)
    src_batch, tgt_batch = next(iter(loader))
    embed_dim = 8
    hidden_dim = 16
    encoder = Encoder(len(vocab_src.itos), embed_dim, hidden_dim)
    decoder = Decoder(len(vocab_tgt.itos), embed_dim, hidden_dim)
    model = Seq2Seq(
        encoder=encoder,
        decoder=decoder,
        pad_idx=vocab_src.pad_idx,
        device=torch.device("cpu"),
    )

    output = model(src_batch, tgt_batch, teacher_forcing_ratio=0.0)
    assert output.shape == (src_batch.size(0), tgt_batch.size(1), len(vocab_tgt.itos))


def test_overfits_tiny_dataset() -> None:
    model, vocab_src, vocab_tgt = train(
        num_epochs=25,
        embed_dim=16,
        hidden_dim=32,
        batch_size=4,
        teacher_forcing_ratio=0.9,
        device=torch.device("cpu"),
    )
    prediction = model.translate(["one", "two"], vocab_src, vocab_tgt)
    assert prediction == ["two", "one"]
