"""A reusable card game engine.

This module provides the generic building blocks that most card games share:

* :class:`Suit` / :class:`Rank` - enumerations describing a standard 52-card deck.
* :class:`Card` - an immutable (suit, rank) pair with a couple of convenience
  helpers.
* :class:`Deck` - a shuffleable, dealable collection of cards.
* :class:`Pile` - an ordered collection used for discard/draw piles and hands.
* :class:`Player` - a named participant that owns a hand of cards.
* :class:`GamePhase` / :class:`GameState` - a small state machine that models the
  ``draw -> play -> discard`` flow of a turn and advances between players.

The engine intentionally knows nothing about the *rules* of a specific game.
Concrete games (see :mod:`main` for a Crazy Eights implementation) build on top
of these primitives.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Iterator, Optional


class Suit(Enum):
    """The four suits of a French-style deck."""

    CLUBS = "♣"
    DIAMONDS = "♦"
    HEARTS = "♥"
    SPADES = "♠"

    @property
    def is_red(self) -> bool:
        return self in (Suit.DIAMONDS, Suit.HEARTS)


class Rank(Enum):
    """Card ranks with an associated numeric value used for ordering."""

    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    @property
    def symbol(self) -> str:
        """A short display string, e.g. ``"A"``, ``"10"`` or ``"K"``."""
        specials = {
            Rank.ACE: "A",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
        }
        return specials.get(self, str(self.value))


@dataclass(frozen=True)
class Card:
    """An immutable playing card.

    Cards are ordered by rank first and suit second which makes sorting a hand
    produce a natural, human-friendly ordering. Because :class:`Rank` and
    :class:`Suit` are plain enums (not orderable), comparison is defined
    explicitly via a numeric sort key.
    """

    rank: Rank = field()
    suit: Suit = field()

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.value}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Card({self.rank.name}, {self.suit.name})"

    @property
    def _sort_key(self) -> tuple[int, int]:
        suit_order = list(Suit).index(self.suit)
        return (self.rank.value, suit_order)

    def __lt__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self._sort_key < other._sort_key

    @property
    def value(self) -> int:
        """The rank's numeric value (Ace low)."""
        return self.rank.value

    def matches(
        self, other: "Card", *, by_suit: bool = True, by_rank: bool = True
    ) -> bool:
        """Return ``True`` when this card shares a suit or rank with ``other``."""
        if by_suit and self.suit == other.suit:
            return True
        if by_rank and self.rank == other.rank:
            return True
        return False


class Deck:
    """A collection of cards that can be shuffled and dealt from the top."""

    def __init__(self, cards: Optional[Iterable[Card]] = None):
        if cards is None:
            self._cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        else:
            self._cards = list(cards)

    @classmethod
    def standard(cls, decks: int = 1) -> "Deck":
        """Build one or more standard 52-card decks combined together."""
        cards: list[Card] = []
        for _ in range(decks):
            cards.extend(Card(rank, suit) for suit in Suit for rank in Rank)
        return cls(cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)

    def __contains__(self, card: object) -> bool:
        return card in self._cards

    @property
    def is_empty(self) -> bool:
        return not self._cards

    def shuffle(self, rng: Optional[random.Random] = None) -> None:
        """Shuffle in place. A seeded ``rng`` makes shuffles reproducible."""
        (rng or random).shuffle(self._cards)

    def deal(self, count: int = 1) -> list[Card]:
        """Remove and return ``count`` cards from the top of the deck."""
        if count < 0:
            raise ValueError("Cannot deal a negative number of cards")
        if count > len(self._cards):
            raise ValueError(
                f"Cannot deal {count} cards; only {len(self._cards)} remain"
            )
        dealt = self._cards[:count]
        self._cards = self._cards[count:]
        return dealt

    def deal_one(self) -> Card:
        """Remove and return a single card from the top of the deck."""
        return self.deal(1)[0]

    def add(self, cards: Iterable[Card]) -> None:
        """Return cards to the bottom of the deck (used when reshuffling)."""
        self._cards.extend(cards)


class Pile:
    """An ordered stack of cards.

    Used both for a player's hand and for shared piles such as the discard
    pile. The "top" of the pile is the most recently added card.
    """

    def __init__(self, cards: Optional[Iterable[Card]] = None):
        self._cards: list[Card] = list(cards) if cards else []

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)

    def __contains__(self, card: object) -> bool:
        return card in self._cards

    def __getitem__(self, index: int) -> Card:
        return self._cards[index]

    @property
    def cards(self) -> list[Card]:
        """A copy of the underlying cards (mutations do not affect the pile)."""
        return list(self._cards)

    @property
    def is_empty(self) -> bool:
        return not self._cards

    @property
    def top(self) -> Optional[Card]:
        """The card on top of the pile, or ``None`` when empty."""
        return self._cards[-1] if self._cards else None

    def add(self, card: Card) -> None:
        self._cards.append(card)

    def add_many(self, cards: Iterable[Card]) -> None:
        self._cards.extend(cards)

    def remove(self, card: Card) -> Card:
        """Remove and return a specific card; raises ``ValueError`` if absent."""
        self._cards.remove(card)
        return card

    def take_top(self) -> Card:
        """Remove and return the top card; raises ``IndexError`` if empty."""
        return self._cards.pop()

    def take_all(self) -> list[Card]:
        """Remove and return every card, leaving the pile empty."""
        cards = self._cards
        self._cards = []
        return cards

    def sort(self) -> None:
        """Sort the pile in place (rank then suit)."""
        self._cards.sort()


class Player:
    """A participant with a name and a hand of cards."""

    def __init__(self, name: str, is_ai: bool = False):
        self.name = name
        self.is_ai = is_ai
        self.hand = Pile()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Player({self.name!r}, cards={len(self.hand)})"

    @property
    def has_won(self) -> bool:
        """A player wins when they have emptied their hand."""
        return self.hand.is_empty

    def draw_from(self, deck: Deck, count: int = 1) -> list[Card]:
        """Draw ``count`` cards from ``deck`` into this player's hand."""
        cards = deck.deal(count)
        self.hand.add_many(cards)
        return cards

    def play(self, card: Card) -> Card:
        """Remove ``card`` from the hand and return it."""
        return self.hand.remove(card)


class GamePhase(Enum):
    """The phases of a single turn plus terminal ``GAME_OVER``."""

    DRAW = "draw"
    PLAY = "play"
    DISCARD = "discard"
    GAME_OVER = "game_over"


class GameState:
    """A small turn-based state machine.

    It tracks whose turn it is, the current :class:`GamePhase`, and provides
    helpers to advance the phase and rotate to the next player. Concrete games
    drive the machine and decide what happens in each phase.
    """

    # The normal within-turn ordering of phases.
    _PHASE_ORDER = (GamePhase.DRAW, GamePhase.PLAY, GamePhase.DISCARD)

    def __init__(self, players: list[Player]):
        if len(players) < 2:
            raise ValueError("A game needs at least two players")
        self.players = players
        self.current_index = 0
        self.phase = GamePhase.DRAW
        self.turn_number = 1
        self.winner: Optional[Player] = None
        self.direction = 1  # 1 = clockwise, -1 = counter-clockwise

    @property
    def current_player(self) -> Player:
        return self.players[self.current_index]

    @property
    def is_over(self) -> bool:
        return self.phase == GamePhase.GAME_OVER

    def reverse_direction(self) -> None:
        """Flip the turn order (useful for games with reverse cards)."""
        self.direction *= -1

    def next_phase(self) -> GamePhase:
        """Advance to the next phase within the current turn.

        Advancing past ``DISCARD`` wraps back to ``DRAW`` but does *not* rotate
        players; call :meth:`end_turn` for that.
        """
        if self.phase == GamePhase.GAME_OVER:
            return self.phase
        index = self._PHASE_ORDER.index(self.phase)
        self.phase = self._PHASE_ORDER[(index + 1) % len(self._PHASE_ORDER)]
        return self.phase

    def set_phase(self, phase: GamePhase) -> None:
        self.phase = phase

    def end_turn(self) -> Player:
        """Rotate to the next player and reset to the ``DRAW`` phase."""
        if self.is_over:
            return self.current_player
        count = len(self.players)
        self.current_index = (self.current_index + self.direction) % count
        self.phase = GamePhase.DRAW
        self.turn_number += 1
        return self.current_player

    def declare_winner(self, player: Player) -> None:
        self.winner = player
        self.phase = GamePhase.GAME_OVER
