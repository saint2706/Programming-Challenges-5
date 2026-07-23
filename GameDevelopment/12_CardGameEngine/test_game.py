"""Tests for the card game engine and the Crazy Eights implementation.

Run with ``pytest`` or directly with ``python test_game.py``. The tests avoid
all I/O so they run headlessly in any environment.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from engine import (
    Card,
    Deck,
    GamePhase,
    GameState,
    Pile,
    Player,
    Rank,
    Suit,
)
from main import WILD_RANK, CrazyEights


# ---------------------------------------------------------------------------
# Engine: Card / Deck / Pile
# ---------------------------------------------------------------------------
def test_card_equality_and_display():
    ace_spades = Card(Rank.ACE, Suit.SPADES)
    assert ace_spades == Card(Rank.ACE, Suit.SPADES)
    assert ace_spades != Card(Rank.ACE, Suit.HEARTS)
    assert str(ace_spades) == "A♠"
    assert ace_spades.value == 1


def test_card_matches():
    a = Card(Rank.KING, Suit.HEARTS)
    assert a.matches(Card(Rank.KING, Suit.CLUBS))  # same rank
    assert a.matches(Card(Rank.TWO, Suit.HEARTS))  # same suit
    assert not a.matches(Card(Rank.TWO, Suit.CLUBS))


def test_standard_deck_has_52_unique_cards():
    deck = Deck.standard()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_deck_shuffle_is_deterministic_with_seed():
    import random

    d1 = Deck.standard()
    d2 = Deck.standard()
    d1.shuffle(random.Random(7))
    d2.shuffle(random.Random(7))
    assert list(d1) == list(d2)


def test_deck_deal_reduces_size_and_preserves_cards():
    deck = Deck.standard()
    hand = deck.deal(5)
    assert len(hand) == 5
    assert len(deck) == 47
    # No card appears both in the dealt hand and the remaining deck.
    assert not set(hand) & set(deck)


def test_deck_deal_too_many_raises():
    deck = Deck(Deck.standard().deal(3))
    try:
        deck.deal(4)
    except ValueError:
        pass
    else:  # pragma: no cover - failure path
        raise AssertionError("dealing more cards than available should raise")


def test_pile_top_and_take():
    pile = Pile()
    assert pile.is_empty and pile.top is None
    pile.add(Card(Rank.TWO, Suit.CLUBS))
    pile.add(Card(Rank.THREE, Suit.CLUBS))
    assert pile.top == Card(Rank.THREE, Suit.CLUBS)
    assert pile.take_top() == Card(Rank.THREE, Suit.CLUBS)
    assert pile.top == Card(Rank.TWO, Suit.CLUBS)


def test_pile_sort_orders_by_rank():
    pile = Pile([Card(Rank.KING, Suit.CLUBS), Card(Rank.TWO, Suit.SPADES)])
    pile.sort()
    assert pile[0].rank == Rank.TWO
    assert pile[1].rank == Rank.KING


# ---------------------------------------------------------------------------
# Engine: Player
# ---------------------------------------------------------------------------
def test_player_draw_and_play():
    deck = Deck.standard()
    player = Player("Test")
    drawn = player.draw_from(deck, 3)
    assert len(player.hand) == 3
    assert not player.has_won
    card = drawn[0]
    player.play(card)
    assert card not in player.hand
    assert len(player.hand) == 2


def test_player_wins_with_empty_hand():
    player = Player("Test")
    assert player.has_won  # no cards == winning condition


# ---------------------------------------------------------------------------
# Engine: GameState machine
# ---------------------------------------------------------------------------
def test_game_state_requires_two_players():
    try:
        GameState([Player("solo")])
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("a single player should be rejected")


def test_phase_cycles_draw_play_discard():
    state = GameState([Player("a"), Player("b")])
    assert state.phase == GamePhase.DRAW
    assert state.next_phase() == GamePhase.PLAY
    assert state.next_phase() == GamePhase.DISCARD
    assert state.next_phase() == GamePhase.DRAW  # wraps around


def test_end_turn_rotates_players():
    a, b = Player("a"), Player("b")
    state = GameState([a, b])
    assert state.current_player is a
    state.end_turn()
    assert state.current_player is b
    assert state.phase == GamePhase.DRAW
    state.end_turn()
    assert state.current_player is a


def test_reverse_direction_changes_rotation():
    a, b, c = Player("a"), Player("b"), Player("c")
    state = GameState([a, b, c])
    state.reverse_direction()
    state.end_turn()
    assert state.current_player is c  # went backwards


def test_declare_winner_ends_game():
    a, b = Player("a"), Player("b")
    state = GameState([a, b])
    state.declare_winner(a)
    assert state.is_over
    assert state.winner is a
    # end_turn is a no-op once the game is over
    assert state.end_turn() is a


# ---------------------------------------------------------------------------
# Crazy Eights game logic
# ---------------------------------------------------------------------------
def make_game(seed=1):
    return CrazyEights([Player("A", is_ai=True), Player("B", is_ai=True)], seed=seed)


def test_game_setup_deals_hands_and_starter():
    game = make_game()
    for player in game.state.players:
        assert len(player.hand) == 5
    assert game.top_card is not None
    # The starter card is never a wild eight.
    assert game.top_card.rank != WILD_RANK
    assert game.active_suit == game.top_card.suit


def test_is_playable_matches_suit_or_rank():
    game = make_game()
    top = game.top_card
    same_suit = Card(Rank.KING if top.rank != Rank.KING else Rank.QUEEN, top.suit)
    assert game.is_playable(same_suit)
    wild = Card(WILD_RANK, Suit.CLUBS)
    assert game.is_playable(wild)  # eights always playable


def test_playing_a_card_moves_it_to_discard():
    game = make_game()
    player = game.state.current_player
    # Force a known playable card into the hand.
    playable = Card(game.top_card.rank, Suit.HEARTS)
    if playable not in player.hand:
        player.hand.add(playable)
    before = len(player.hand)
    game.play_card(player, playable)
    assert playable not in player.hand
    assert game.discard.top == playable
    assert len(player.hand) == before - 1


def test_illegal_play_raises():
    game = make_game()
    player = game.state.current_player
    # Build a card that matches neither suit nor rank and is not wild.
    bad_rank = next(r for r in Rank if r not in (game.top_card.rank, WILD_RANK))
    bad_suit = next(s for s in Suit if s != game.active_suit)
    bad = Card(bad_rank, bad_suit)
    player.hand.add(bad)
    try:
        game.play_card(player, bad)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("illegal play should raise ValueError")


def test_wild_eight_sets_active_suit():
    game = make_game()
    player = game.state.current_player
    eight = Card(WILD_RANK, Suit.CLUBS)
    player.hand.add(eight)
    game.play_card(player, eight, chosen_suit=Suit.DIAMONDS)
    assert game.active_suit == Suit.DIAMONDS
    assert game.top_card == eight


def test_draw_adds_to_hand():
    game = make_game()
    player = game.state.current_player
    before = len(player.hand)
    drawn = game.draw_card(player)
    assert drawn is not None
    assert len(player.hand) == before + 1


def test_ai_move_prefers_non_wild():
    game = make_game()
    player = game.state.current_player
    player.hand.take_all()
    non_wild = Card(game.top_card.rank, Suit.HEARTS)
    wild = Card(WILD_RANK, Suit.SPADES)
    player.hand.add_many([wild, non_wild])
    move = game.ai_choose_move(player)
    assert move is not None
    card, _ = move
    assert card.rank != WILD_RANK  # should keep the eight in reserve


def test_full_ai_game_terminates_with_winner():
    game = make_game(seed=123)
    state = game.state
    safety = 0
    while not state.is_over and safety < 10_000:
        player = state.current_player
        game.take_ai_turn(player)
        if not player.has_won:
            state.end_turn()
        safety += 1
    assert state.is_over, "AI game should reach a terminal state"
    assert state.winner is not None
    assert state.winner.has_won


def run_all_tests():
    print("\n=== Running Card Game Engine Tests ===\n")
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except Exception as exc:  # pragma: no cover - reporting path
            failures += 1
            print(f"✗ {test.__name__}: {exc}")
    if failures:
        print(f"\n✗ {failures} test(s) failed\n")
        return False
    print(f"\n=== All {len(tests)} tests passed! ✓ ===\n")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
