from __future__ import annotations

"""Toy Neural Machine Translation model with attention.

This module implements a small encoder-decoder LSTM with dot-product
attention on a synthetic parallel corpus of short token sequences. It is
self-contained: building the dataset, defining vocabularies, training the
model, and running sample translations can all be done by executing the
file directly.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import torch
from torch import Tensor, nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@dataclass
class Vocabulary:
    """Simple vocabulary helper for token-to-id mappings."""

    stoi: Dict[str, int]
    itos: List[str]

    @classmethod
    def build(cls, sentences: Iterable[Sequence[str]]) -> "Vocabulary":
        """Create a vocabulary from an iterable of tokenized sentences."""

        tokens = {token for sentence in sentences for token in sentence}
        specials = ["<pad>", "<sos>", "<eos>"]
        itos = specials + sorted(tokens)
        stoi = {token: idx for idx, token in enumerate(itos)}
        return cls(stoi=stoi, itos=itos)

    @property
    def pad_idx(self) -> int:
        return self.stoi["<pad>"]

    @property
    def sos_idx(self) -> int:
        return self.stoi["<sos>"]

    @property
    def eos_idx(self) -> int:
        return self.stoi["<eos>"]

    def numericalize(self, tokens: Sequence[str]) -> List[int]:
        return [self.stoi[token] for token in tokens]

    def denumericalize(self, indices: Sequence[int]) -> List[str]:
        return [self.itos[idx] for idx in indices]


class SyntheticTranslationDataset(Dataset[Tuple[Tensor, Tensor]]):
    """Synthetic parallel dataset mapping digit words to reversed sequences."""

    def __init__(self, pairs: List[Tuple[List[str], List[str]]], vocab_src: Vocabulary, vocab_tgt: Vocabulary):
        self.pairs = pairs
        self.vocab_src = vocab_src
        self.vocab_tgt = vocab_tgt

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int) -> Tuple[Tensor, Tensor]:
        src_tokens, tgt_tokens = self.pairs[idx]
        src_ids = torch.tensor(self.vocab_src.numericalize(src_tokens), dtype=torch.long)
        tgt_ids = torch.tensor(
            [self.vocab_tgt.sos_idx] + self.vocab_tgt.numericalize(tgt_tokens) + [self.vocab_tgt.eos_idx],
            dtype=torch.long,
        )
        return src_ids, tgt_ids

    def collate_fn(self, batch: List[Tuple[Tensor, Tensor]]) -> Tuple[Tensor, Tensor]:
        src_batch, tgt_batch = zip(*batch)
        src_padded = pad_sequence(src_batch, batch_first=True, padding_value=self.vocab_src.pad_idx)
        tgt_padded = pad_sequence(tgt_batch, batch_first=True, padding_value=self.vocab_tgt.pad_idx)
        return src_padded, tgt_padded


class Encoder(nn.Module):
    """Encoder LSTM that returns outputs for attention and final hidden state."""

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int = 1) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers, batch_first=True)

    def forward(self, src: Tensor) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:
        embedded = self.embedding(src)
        outputs, (hidden, cell) = self.rnn(embedded)
        return outputs, (hidden, cell)


class Attention(nn.Module):
    """Dot-product attention mechanism with padding mask."""

    def forward(self, decoder_hidden: Tensor, encoder_outputs: Tensor, src_mask: Tensor) -> Tensor:
        scores = torch.bmm(encoder_outputs, decoder_hidden.unsqueeze(2)).squeeze(2)
        scores.masked_fill_(~src_mask, float("-inf"))
        attn_weights = torch.softmax(scores, dim=1)
        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs).squeeze(1)
        return context


class Decoder(nn.Module):
    """Decoder LSTM with attention."""

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int = 1) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.LSTM(embed_dim + hidden_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim * 2, vocab_size)
        self.attention = Attention()

    def forward(
        self,
        input_token: Tensor,
        hidden: Tensor,
        cell: Tensor,
        encoder_outputs: Tensor,
        src_mask: Tensor,
    ) -> Tuple[Tensor, Tensor, Tensor]:
        embedded = self.embedding(input_token.unsqueeze(1))
        context = self.attention(hidden[-1], encoder_outputs, src_mask)
        rnn_input = torch.cat([embedded, context.unsqueeze(1)], dim=2)
        output, (hidden, cell) = self.rnn(rnn_input, (hidden, cell))
        prediction = self.fc_out(torch.cat([output.squeeze(1), context], dim=1))
        return prediction, hidden, cell


class Seq2Seq(nn.Module):
    """Full sequence-to-sequence model wiring encoder and decoder."""

    def __init__(self, encoder: Encoder, decoder: Decoder, pad_idx: int, device: torch.device) -> None:
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.pad_idx = pad_idx
        self.device = device

    def forward(self, src: Tensor, tgt: Tensor, teacher_forcing_ratio: float = 0.5) -> Tensor:
        batch_size, tgt_len = tgt.size()
        vocab_size = self.decoder.fc_out.out_features
        outputs = torch.zeros(batch_size, tgt_len, vocab_size, device=self.device)
        encoder_outputs, (hidden, cell) = self.encoder(src)
        input_token = tgt[:, 0]
        src_mask = src != self.pad_idx
        for t in range(1, tgt_len):
            output, hidden, cell = self.decoder(input_token, hidden, cell, encoder_outputs, src_mask)
            outputs[:, t] = output
            teacher_force = torch.rand(1).item() < teacher_forcing_ratio
            top1 = output.argmax(1)
            input_token = tgt[:, t] if teacher_force else top1
        return outputs

    def translate(
        self, src_sentence: Sequence[str], vocab_src: Vocabulary, vocab_tgt: Vocabulary, max_len: int = 15
    ) -> List[str]:
        self.eval()
        with torch.no_grad():
            src_tensor = torch.tensor(vocab_src.numericalize(src_sentence), dtype=torch.long, device=self.device).unsqueeze(0)
            encoder_outputs, (hidden, cell) = self.encoder(src_tensor)
            input_token = torch.tensor([vocab_tgt.sos_idx], device=self.device)
            src_mask = src_tensor != self.pad_idx
            outputs: List[int] = []
            for _ in range(max_len):
                output, hidden, cell = self.decoder(input_token, hidden, cell, encoder_outputs, src_mask)
                top1 = output.argmax(1)
                if top1.item() == vocab_tgt.eos_idx:
                    break
                outputs.append(top1.item())
                input_token = top1
        return vocab_tgt.denumericalize(outputs)


def build_synthetic_pairs() -> List[Tuple[List[str], List[str]]]:
    """Create a tiny synthetic dataset of digit sequences and reversed translations."""

    digits = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    pairs: List[Tuple[List[str], List[str]]] = []
    for length in range(2, 5):
        for start in range(0, 10 - length):
            src = digits[start : start + length]
            tgt = list(reversed(src))
            pairs.append((src, tgt))
    return pairs


def create_dataloaders(batch_size: int = 4) -> Tuple[DataLoader, Vocabulary, Vocabulary]:
    """Build dataloaders and vocabularies for the synthetic data."""

    pairs = build_synthetic_pairs()
    vocab_src = Vocabulary.build(src for src, _ in pairs)
    vocab_tgt = Vocabulary.build(tgt for _, tgt in pairs)
    dataset = SyntheticTranslationDataset(pairs, vocab_src, vocab_tgt)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, collate_fn=dataset.collate_fn)
    return loader, vocab_src, vocab_tgt


def train(
    num_epochs: int = 50,
    embed_dim: int = 32,
    hidden_dim: int = 64,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
    teacher_forcing_ratio: float = 0.7,
    device: torch.device | None = None,
) -> Tuple[Seq2Seq, Vocabulary, Vocabulary]:
    """Train the toy NMT model on the synthetic dataset."""

    set_seed(42)
    train_device = device or DEVICE
    loader, vocab_src, vocab_tgt = create_dataloaders(batch_size=batch_size)
    encoder = Encoder(len(vocab_src.itos), embed_dim, hidden_dim).to(train_device)
    decoder = Decoder(len(vocab_tgt.itos), embed_dim, hidden_dim).to(train_device)
    model = Seq2Seq(encoder, decoder, pad_idx=vocab_src.pad_idx, device=train_device).to(train_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss(ignore_index=vocab_tgt.pad_idx)

    model.train()
    for _ in range(num_epochs):
        for src_batch, tgt_batch in loader:
            src_batch = src_batch.to(train_device)
            tgt_batch = tgt_batch.to(train_device)
            optimizer.zero_grad()
            output = model(src_batch, tgt_batch, teacher_forcing_ratio=teacher_forcing_ratio)
            output_dim = output.shape[-1]
            output_flat = output[:, 1:].reshape(-1, output_dim)
            tgt_flat = tgt_batch[:, 1:].reshape(-1)
            loss = criterion(output_flat, tgt_flat)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
    return model, vocab_src, vocab_tgt


def demo_translations(model: Seq2Seq, vocab_src: Vocabulary, vocab_tgt: Vocabulary) -> List[Tuple[str, str]]:
    """Generate a few sample translations for inspection."""

    samples = [["one", "two", "three"], ["four", "five"], ["six", "seven", "eight", "nine"]]
    translations: List[Tuple[str, str]] = []
    for src in samples:
        pred_tokens = model.translate(src, vocab_src, vocab_tgt)
        translations.append((" ".join(src), " ".join(pred_tokens)))
    return translations


if __name__ == "__main__":
    trained_model, src_vocab, tgt_vocab = train()
    print("Sample translations after training:")
    for src, tgt in demo_translations(trained_model, src_vocab, tgt_vocab):
        print(f"{src} -> {tgt}")
