# Card Game Engine

A reusable, game-agnostic card engine plus a fully playable **Crazy Eights**
game built on top of it. The engine models the pieces every card game shares —
cards, decks, piles, players and a turn-based state machine — while the rules of
any specific game live separately.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Gameplay](#gameplay)
- [Testing](#testing)

## ✨ Features

- **Generic engine** (`engine.py`): `Card`, `Deck`, `Pile`, `Player` and a
  `GameState` turn machine (`draw → play → discard`) with player rotation and
  reversible direction — no game-specific rules baked in.
- **Standard 52-card deck** with suits, ranks, ordering and seedable shuffling
  for reproducible games.
- **Crazy Eights** (`main.py`): a complete game demonstrating the engine —
  suit/rank matching, wild eights that let you nominate the next suit, drawing
  when stuck, and automatic reshuffling of the discard pile.
- **Simple AI opponent** that plays low cards first and keeps wild eights in
  reserve.
- **Command-line interface** with a human-vs-AI mode and an AI-vs-AI demo mode.
- **Pure-Python, no external dependencies** — the logic is I/O-free and fully
  unit tested.

## 🏗️ Architecture

```
engine.py   Generic building blocks (reusable across card games)
 ├─ Suit / Rank      Enumerations for a French-style deck
 ├─ Card             Immutable (rank, suit) pair, ordered by rank then suit
 ├─ Deck             Shuffle / deal / recycle
 ├─ Pile             Ordered stack used for hands and the discard pile
 ├─ Player           Name + hand, with draw/play helpers
 └─ GameState        Turn state machine: phases, rotation, winner

main.py     Crazy Eights, a concrete game on top of the engine
 ├─ CrazyEights      Rules engine (legal moves, play/draw, AI, win detection)
 └─ CrazyEightsCLI   Presentation + input handling
```

To build a different game (Go Fish, War, Uno-like, …) you reuse everything in
`engine.py` and write a new rules class in the style of `CrazyEights`.

## 💻 Installation

Requires only Python 3.10+ (standard library):

```bash
cd GameDevelopment/12_CardGameEngine
```

No `pip install` is necessary.

## 🚀 Usage

```bash
python main.py            # play against the computer
python main.py --demo     # watch two AIs play automatically
python main.py --seed 42  # reproducible shuffle (useful for demos/debugging)
```

During your turn, playable cards are marked with `*`. Enter a card's number to
play it, or `d` to draw from the stock. When you play an eight you'll be asked
which suit the next player must follow.

## 🎮 Gameplay

Crazy Eights rules as implemented:

1. Each player starts with **5 cards**; one card is turned up to start the
   discard pile.
2. On your turn, play a card that matches the **suit or rank** of the top card.
3. **Eights are wild** — play one on anything, then nominate the suit to follow.
4. If you can't play, **draw** from the stock until you can (or the stock runs
   out, in which case you pass). The discard pile is reshuffled into the stock
   when the stock is empty.
5. The first player to **empty their hand wins**.

## 🧪 Testing

The engine and game logic are covered by an I/O-free test suite:

```bash
python test_game.py        # standalone runner with tick-marks
# or
python -m pytest test_game.py
```
