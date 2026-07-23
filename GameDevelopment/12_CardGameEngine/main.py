"""Crazy Eights - a playable card game built on the generic card engine.

This module demonstrates the :mod:`engine` primitives (``Card``, ``Deck``,
``Player``, ``GameState``) by implementing the classic game of Crazy Eights and
wrapping it in a small command-line interface with a simple AI opponent.

Rules implemented
-----------------
* Each player is dealt an opening hand (5 cards for two players).
* On your turn you must play a card that matches the suit or rank of the top of
  the discard pile.
* Eights are wild: you may play an eight on anything and then nominate the suit
  that the next player must follow.
* If you cannot (or choose not to) play, you draw from the stock until you can
  play or the stock is exhausted.
* First player to empty their hand wins.

Run it with::

    python main.py            # human vs AI
    python main.py --demo     # watch two AIs play automatically
    python main.py --seed 42  # reproducible shuffle

The heavy lifting lives in :class:`CrazyEights`, which is fully testable without
any I/O; :class:`CrazyEightsCLI` only adds presentation and input handling.
"""

from __future__ import annotations

import argparse
import random
from typing import Optional

from engine import Card, Deck, GameState, Pile, Player, Rank, Suit

WILD_RANK = Rank.EIGHT
STARTING_HAND_SIZE = 5


class CrazyEights:
    """Rules engine for a game of Crazy Eights.

    The class owns the deck, discard pile and turn state, and exposes methods
    that a UI (or a test) can call: :meth:`legal_moves`, :meth:`play_card`,
    :meth:`draw_card` and :meth:`ai_choose_move`.
    """

    def __init__(self, players: list[Player], seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.state = GameState(players)
        self.stock = Deck.standard()
        self.stock.shuffle(self.rng)
        self.discard = Pile()
        # The suit that must currently be followed. Normally the top card's
        # suit, but an eight lets the player override it.
        self.active_suit: Optional[Suit] = None
        self._deal_opening_hands()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _deal_opening_hands(self) -> None:
        for player in self.state.players:
            player.draw_from(self.stock, STARTING_HAND_SIZE)
        # Turn over the first card to start the discard pile. Keep drawing if
        # it happens to be a wild eight so the opening suit is unambiguous.
        first = self.stock.deal_one()
        while first.rank == WILD_RANK:
            self.stock.add([first])
            self.stock.shuffle(self.rng)
            first = self.stock.deal_one()
        self.discard.add(first)
        self.active_suit = first.suit

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @property
    def top_card(self) -> Card:
        top = self.discard.top
        assert top is not None  # discard always has the starter card
        return top

    def is_playable(self, card: Card) -> bool:
        """Return ``True`` if ``card`` may legally be played right now."""
        if card.rank == WILD_RANK:
            return True  # eights are always playable
        return card.suit == self.active_suit or card.rank == self.top_card.rank

    def legal_moves(self, player: Player) -> list[Card]:
        """All cards in ``player``'s hand that are currently playable."""
        return [card for card in player.hand if self.is_playable(card)]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def draw_card(self, player: Player) -> Optional[Card]:
        """Draw a single card for ``player``; reshuffles the discard if needed.

        Returns the drawn card, or ``None`` if the stock is exhausted and there
        is nothing to reshuffle.
        """
        if self.stock.is_empty:
            self._replenish_stock()
        if self.stock.is_empty:
            return None
        (card,) = player.draw_from(self.stock, 1)
        return card

    def _replenish_stock(self) -> None:
        """Recycle the discard pile (keeping its top card) into the stock."""
        if len(self.discard) <= 1:
            return
        top = self.discard.take_top()
        recycled = self.discard.take_all()
        self.discard.add(top)
        self.stock.add(recycled)
        self.stock.shuffle(self.rng)

    def play_card(
        self, player: Player, card: Card, chosen_suit: Optional[Suit] = None
    ) -> None:
        """Play ``card`` from ``player``'s hand onto the discard pile.

        ``chosen_suit`` is required when playing a wild eight and ignored
        otherwise. Raises ``ValueError`` for illegal moves.
        """
        if card not in player.hand:
            raise ValueError(f"{player.name} does not hold {card}")
        if not self.is_playable(card):
            raise ValueError(
                f"{card} does not match {self.top_card} (suit {self.active_suit.value})"
            )

        player.play(card)
        self.discard.add(card)

        if card.rank == WILD_RANK:
            if chosen_suit is None:
                # Default to the most common suit left in hand (or the card's).
                chosen_suit = self._best_suit(player) or card.suit
            self.active_suit = chosen_suit
        else:
            self.active_suit = card.suit

        if player.has_won:
            self.state.declare_winner(player)

    def _best_suit(self, player: Player) -> Optional[Suit]:
        """The suit the player holds most of (used for AI wild-card choice)."""
        counts: dict[Suit, int] = {}
        for card in player.hand:
            if card.rank == WILD_RANK:
                continue
            counts[card.suit] = counts.get(card.suit, 0) + 1
        if not counts:
            return None
        return max(counts, key=lambda s: counts[s])

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def ai_choose_move(self, player: Player) -> Optional[tuple[Card, Optional[Suit]]]:
        """Pick a move for an AI ``player``.

        Prefers playing a non-wild card (saving eights for when they are
        needed). Returns ``(card, chosen_suit)`` or ``None`` to signal a draw.
        """
        moves = self.legal_moves(player)
        if not moves:
            return None
        non_wild = [c for c in moves if c.rank != WILD_RANK]
        if non_wild:
            # Play the lowest-value matching card to shed points early.
            card = min(non_wild, key=lambda c: c.value)
            return card, None
        # Only wild eights available; nominate our strongest suit.
        card = moves[0]
        return card, self._best_suit(player) or card.suit

    def take_ai_turn(self, player: Player) -> str:
        """Run a complete AI turn and return a short human-readable summary."""
        move = self.ai_choose_move(player)
        drew = 0
        while move is None and not self.stock.is_empty:
            self.draw_card(player)
            drew += 1
            move = self.ai_choose_move(player)
        if move is None:
            return f"{player.name} draws but cannot play and passes."
        card, suit = move
        self.play_card(player, card, suit)
        prefix = f"{player.name} draws {drew} then " if drew else f"{player.name} "
        if card.rank == WILD_RANK:
            return f"{prefix}plays {card} and calls {self.active_suit.name.title()}."
        return f"{prefix}plays {card}."


class CrazyEightsCLI:
    """A thin command-line front-end around :class:`CrazyEights`."""

    def __init__(self, game: CrazyEights):
        self.game = game

    def run(self) -> Player:
        state = self.game.state
        print("=" * 48)
        print("  CRAZY EIGHTS")
        print("=" * 48)
        while not state.is_over:
            player = state.current_player
            self._show_table(player)
            if player.is_ai:
                summary = self.game.take_ai_turn(player)
                print(f"  {summary}")
            else:
                self._human_turn(player)
            if not player.has_won:
                state.end_turn()
        winner = state.winner
        assert winner is not None
        print("\n" + "=" * 48)
        print(f"  🏆 {winner.name} wins!")
        print("=" * 48)
        return winner

    def _show_table(self, player: Player) -> None:
        print("\n" + "-" * 48)
        print(f"Turn {self.game.state.turn_number}: {player.name}")
        print(
            f"Top of pile: {self.game.top_card}  |  Suit to follow: {self.game.active_suit.value}"
        )
        counts = ", ".join(
            f"{p.name}: {len(p.hand)}"
            for p in self.game.state.players
            if p is not player
        )
        print(f"Opponents' cards -> {counts}")

    def _human_turn(self, player: Player) -> None:
        player.hand.sort()
        while True:
            legal = self.game.legal_moves(player)
            hand_display = "  ".join(
                f"[{i}]{card}{'*' if self.game.is_playable(card) else ' '}"
                for i, card in enumerate(player.hand)
            )
            print(f"Your hand: {hand_display}")
            print("  (* = playable)  Enter card number, or 'd' to draw.")
            if not legal:
                print("  No playable cards - you must draw.")
            choice = input("> ").strip().lower()
            if choice == "d":
                card = self.game.draw_card(player)
                if card is None:
                    print("  Stock empty - you pass.")
                    return
                print(f"  You drew {card}.")
                if not self.game.is_playable(card):
                    continue
                # Auto-offer to play the freshly drawn card.
                continue
            if not choice.isdigit():
                print("  Please enter a valid number or 'd'.")
                continue
            index = int(choice)
            if index < 0 or index >= len(player.hand):
                print("  That card number is out of range.")
                continue
            card = player.hand[index]
            if not self.game.is_playable(card):
                print(f"  {card} does not match. Try again.")
                continue
            chosen_suit = None
            if card.rank == WILD_RANK:
                chosen_suit = self._ask_suit()
            self.game.play_card(player, card, chosen_suit)
            if card.rank == WILD_RANK:
                print(
                    f"  You played {card} and called {self.game.active_suit.name.title()}."
                )
            else:
                print(f"  You played {card}.")
            return

    def _ask_suit(self) -> Suit:
        options = list(Suit)
        labels = "  ".join(
            f"[{i}]{s.name.title()}{s.value}" for i, s in enumerate(options)
        )
        while True:
            print(f"  Choose a suit: {labels}")
            choice = input("  suit> ").strip()
            if choice.isdigit() and 0 <= int(choice) < len(options):
                return options[int(choice)]
            print("  Invalid suit choice.")


def build_game(demo: bool, seed: Optional[int]) -> CrazyEights:
    """Create a two-player game (human vs AI, or AI vs AI in demo mode)."""
    if demo:
        players = [Player("Ada (AI)", is_ai=True), Player("Bea (AI)", is_ai=True)]
    else:
        players = [Player("You", is_ai=False), Player("Computer", is_ai=True)]
    return CrazyEights(players, seed=seed)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Play Crazy Eights on the card engine."
    )
    parser.add_argument(
        "--demo", action="store_true", help="watch two AI players compete automatically"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="seed the shuffle for reproducibility"
    )
    args = parser.parse_args()

    game = build_game(demo=args.demo, seed=args.seed)
    CrazyEightsCLI(game).run()


if __name__ == "__main__":
    main()
