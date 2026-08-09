"""Headless tests for the board games, the bot, the protocol and the lobby.

Nothing here imports :mod:`pygame` or opens a socket: the lobby is driven
through fake connections that just collect the dicts sent to them, which is the
whole point of keeping :mod:`lobby` transport-agnostic.

Run with ``pytest`` or directly with ``python test_game.py``.
"""

import importlib
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_CHALLENGE_PKG = "GameDevelopment.14_OnlineMultiplayer"

boardgames = importlib.import_module(f"{_CHALLENGE_PKG}.boardgames")
sys.modules["boardgames"] = boardgames
ConnectFour = boardgames.ConnectFour
IllegalMove = boardgames.IllegalMove
Mark = boardgames.Mark
TicTacToe = boardgames.TicTacToe
create_game = boardgames.create_game
normalise_game_key = boardgames.normalise_game_key
render_ascii = boardgames.render_ascii

proto = importlib.import_module(f"{_CHALLENGE_PKG}.protocol")
sys.modules["protocol"] = proto

_ai = importlib.import_module(f"{_CHALLENGE_PKG}.ai")
Bot = _ai.Bot
BotConfig = _ai.BotConfig
Difficulty = _ai.Difficulty

_lobby = importlib.import_module(f"{_CHALLENGE_PKG}.lobby")
Lobby = _lobby.Lobby
Room = _lobby.Room


# ---------------------------------------------------------------------------
# Tic-Tac-Toe rules
# ---------------------------------------------------------------------------
def test_tictactoe_starts_empty():
    game = TicTacToe()
    assert game.legal_moves() == list(range(9))
    assert game.turn is Mark.P1
    assert not game.is_over
    assert game.empty_count == 9


def test_tictactoe_alternates_turns():
    game = TicTacToe()
    game.play(0)
    assert game.turn is Mark.P2
    game.play(1)
    assert game.turn is Mark.P1
    assert game.cells[0] is Mark.P1 and game.cells[1] is Mark.P2


def test_tictactoe_rejects_occupied_and_finished():
    game = TicTacToe()
    game.play(4)
    try:
        game.play(4)
    except IllegalMove:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("replaying a cell should be illegal")


def test_tictactoe_row_win_records_line():
    game = TicTacToe()
    for move in (0, 3, 1, 4, 2):  # X takes the top row
        game.play(move)
    assert game.winner is Mark.P1
    assert game.win_cells == (0, 1, 2)
    assert game.legal_moves() == []
    assert game.is_over and not game.is_draw


def test_tictactoe_diagonal_win():
    game = TicTacToe()
    for move in (0, 1, 4, 2, 8):
        game.play(move)
    assert game.winner is Mark.P1
    assert game.win_cells == (0, 4, 8)


def test_tictactoe_draw():
    game = TicTacToe()
    for move in (4, 0, 1, 7, 3, 5, 2, 6, 8):
        game.play(move)
    assert game.winner is None
    assert game.is_draw and game.is_over


def test_tictactoe_undo_restores_position():
    game = TicTacToe()
    game.play(4)
    game.play(0)
    snapshot = list(game.cells)
    game.play(8)
    game.undo()
    assert list(game.cells) == snapshot
    assert game.turn is Mark.P1
    assert game.winner is None


def test_tictactoe_undo_clears_a_win():
    game = TicTacToe()
    for move in (0, 3, 1, 4, 2):
        game.play(move)
    assert game.winner is Mark.P1
    game.undo()
    assert game.winner is None
    assert game.turn is Mark.P1
    assert 2 in game.legal_moves()


def test_tictactoe_parse_move_accepts_numbers_and_coordinates():
    game = TicTacToe()
    assert game.parse_move("5") == 4
    assert game.parse_move("b2") == 4
    assert game.parse_move("B2") == 4
    assert game.parse_move("a1") == 0
    assert game.parse_move("c3") == 8
    try:
        game.parse_move("zz")
    except IllegalMove:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("nonsense input should raise")


def test_tictactoe_generalises_to_bigger_boards():
    game = TicTacToe(size=4, connect=4)
    for move in (0, 4, 1, 5, 2, 6, 3):
        game.play(move)
    assert game.winner is Mark.P1
    assert len(game.win_cells) == 4


# ---------------------------------------------------------------------------
# Connect Four rules
# ---------------------------------------------------------------------------
def test_connect4_discs_stack_from_the_bottom():
    game = ConnectFour()
    game.play(3)
    assert game.at(5, 3) is Mark.P1
    game.play(3)
    assert game.at(4, 3) is Mark.P2
    assert game.column_height(3) == 2


def test_connect4_full_column_is_illegal():
    game = ConnectFour()
    for _ in range(6):
        game.play(0)
    assert 0 not in game.legal_moves()
    try:
        game.play(0)
    except IllegalMove:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("a full column should be rejected")


def test_connect4_vertical_win():
    game = ConnectFour()
    for _ in range(3):
        game.play(2)
        game.play(3)
    game.play(2)
    assert game.winner is Mark.P1
    assert len(game.win_cells) == 4


def test_connect4_horizontal_win():
    game = ConnectFour()
    for col in range(3):
        game.play(col)
        game.play(col)
    game.play(3)
    assert game.winner is Mark.P1


def test_connect4_diagonal_win():
    game = ConnectFour()
    # Build a staircase so P1 completes a rising diagonal from (5,0).
    for move in (0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3):
        game.play(move)
    assert game.winner is Mark.P1
    assert len(game.win_cells) == 4


def test_connect4_undo_pops_the_top_disc():
    game = ConnectFour()
    game.play(3)
    game.play(3)
    game.undo()
    assert game.at(4, 3) is Mark.EMPTY
    assert game.at(5, 3) is Mark.P1
    assert game.turn is Mark.P2


def test_connect4_draw_on_full_board():
    # A 3x3 board with connect=4 cannot be won, so filling it must draw.
    game = ConnectFour(rows=3, cols=3, connect=4)
    for col in (0, 0, 0, 1, 1, 1, 2, 2, 2):
        game.play(col)
    assert game.empty_count == 0
    assert game.winner is None
    assert game.is_draw and game.is_over
    assert game.legal_moves() == []


def test_connect4_parse_move_is_one_based():
    game = ConnectFour()
    assert game.parse_move("1") == 0
    assert game.parse_move("7") == 6
    assert game.move_label(0) == "1"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def test_create_game_accepts_aliases():
    assert isinstance(create_game("ttt"), TicTacToe)
    assert isinstance(create_game("c4"), ConnectFour)
    assert normalise_game_key("Connect-4") == "connect4"


def test_serialisation_round_trip():
    game = ConnectFour()
    for move in (3, 3, 4, 2, 5):
        game.play(move)
    payload = game.to_dict()
    clone = ConnectFour.from_dict(payload)
    assert list(clone.cells) == list(game.cells)
    assert clone.turn is game.turn
    assert clone.history == game.history


def test_copy_is_independent():
    game = TicTacToe()
    game.play(0)
    clone = game.copy()
    clone.play(1)
    assert game.cells[1] is Mark.EMPTY
    assert len(game.history) == 1


def test_render_ascii_has_a_row_per_line():
    game = ConnectFour()
    game.play(0)
    text = render_ascii(game, marks=("R", "Y"))
    lines = text.splitlines()
    assert len(lines) == game.rows + 1  # header + rows
    assert "R" in lines[-1]


def test_open_windows_excludes_blocked_lines():
    game = TicTacToe()
    game.play(0)  # P1 top-left
    game.play(1)  # P2 blocks the top row
    for window in game.open_windows(Mark.P1):
        assert 1 not in window


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------
def test_bot_does_not_mutate_the_game():
    game = TicTacToe()
    game.play(4)
    before = (list(game.cells), game.turn, list(game.history))
    Bot(Difficulty.HARD, rng=random.Random(1)).choose(game)
    assert (list(game.cells), game.turn, list(game.history)) == before


def test_bot_takes_an_immediate_win():
    game = TicTacToe()
    for move in (0, 3, 1, 4):  # X has 0,1 — X to move, 2 wins
        game.play(move)
    assert Bot(Difficulty.HARD, rng=random.Random(2)).choose(game) == 2


def test_bot_blocks_an_immediate_threat():
    game = TicTacToe()
    for move in (0, 4, 1):  # X threatens cell 2; O must block
        game.play(move)
    assert Bot(Difficulty.HARD, rng=random.Random(3)).choose(game) == 2


def test_hard_bot_never_loses_tictactoe():
    """Perfect play means every game against a random mover is a draw or win."""
    rng = random.Random(7)
    for trial in range(12):
        bot = Bot(Difficulty.HARD, rng=random.Random(100 + trial))
        bot_mark = Mark.P1 if trial % 2 == 0 else Mark.P2
        game = TicTacToe()
        while not game.is_over:
            if game.turn is bot_mark:
                game.play(bot.choose(game))
            else:
                game.play(rng.choice(game.legal_moves()))
        assert game.winner in (None, bot_mark), f"bot lost trial {trial}"


def test_bot_finds_a_connect4_win():
    game = ConnectFour()
    for move in (3, 0, 4, 1, 5):  # P1 has 3,4,5 on the bottom row
        game.play(move)
    game.play(0)  # back to P1 with 2 and 6 both winning
    assert Bot(Difficulty.MEDIUM, rng=random.Random(5)).choose(game) in (2, 6)


def test_bot_blocks_a_connect4_threat():
    game = ConnectFour()
    for move in (3, 0, 4, 1, 5):  # P1 threatens columns 2 and 6...
        game.play(move)
    # ...but it is P2's move here, and P2 must stop one of them.
    assert Bot(Difficulty.HARD, rng=random.Random(6)).choose(game) in (2, 6)


def test_easy_bot_still_returns_legal_moves():
    game = ConnectFour()
    bot = Bot(Difficulty.EASY, rng=random.Random(11))
    for _ in range(10):
        if game.is_over:
            break
        move = bot.choose(game)
        assert move in game.legal_moves()
        game.play(move)


def test_bot_config_override_limits_search():
    game = ConnectFour()
    bot = Bot(config=BotConfig(max_depth=1, time_limit=0.05), rng=random.Random(1))
    bot.choose(game)
    assert bot.depth_reached == 1
    assert bot.nodes > 0


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------
def test_protocol_round_trip():
    frame = proto.encode(proto.message(proto.MOVE, move=3))
    decoded = proto.decode(frame)
    assert decoded == {"type": "move", "move": 3}


def test_protocol_rejects_malformed_frames():
    for bad in ("not json", "[1,2]", '{"no":"type"}'):
        try:
            proto.decode(bad)
        except proto.ProtocolError:
            continue
        raise AssertionError(f"{bad!r} should not decode")  # pragma: no cover


def test_protocol_require_rejects_booleans_for_ints():
    try:
        proto.require({"move": True}, "move", int)
    except proto.ProtocolError:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("True must not pass as an integer move")


def test_protocol_require_reports_missing_fields():
    try:
        proto.require({}, "code", str)
    except proto.ProtocolError as exc:
        assert "code" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("missing field should raise")


# ---------------------------------------------------------------------------
# Lobby
# ---------------------------------------------------------------------------
class FakeConnection:
    """Collects the messages the lobby sends to one client."""

    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)

    def of_type(self, kind):
        return [m for m in self.messages if m.get("type") == kind]

    def last(self, kind):
        found = self.of_type(kind)
        return found[-1] if found else None

    def errors(self):
        return [m["code"] for m in self.of_type(proto.ERROR)]


def make_lobby(seed=0):
    return Lobby(rng=random.Random(seed), reconnect_grace=10.0)


def join(lobby, name):
    """Connect a client and complete the handshake."""
    conn = FakeConnection()
    session = lobby.connect(conn.send)
    lobby.handle(session, proto.message(proto.HELLO, name=name))
    return conn, session


def test_hello_returns_a_welcome_with_a_token():
    lobby = make_lobby()
    conn, _ = join(lobby, "ada")
    welcome = conn.last(proto.WELCOME)
    assert welcome is not None
    assert welcome["token"]
    assert "tictactoe" in welcome["games"]


def test_create_and_join_room_seats_two_players():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]

    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    state = guest_conn.last(proto.ROOM_STATE)
    assert state["code"] == code
    assert state["seat"] == 1
    assert [p["online"] for p in state["players"]] == [True, True]
    assert host.seat == 0 and guest.seat == 1


def test_joining_an_unknown_room_errors():
    lobby = make_lobby()
    conn, session = join(lobby, "lost")
    lobby.handle(session, proto.message(proto.JOIN_ROOM, code="ZZZZ"))
    assert proto.ERR_NO_ROOM in conn.errors()


def test_moves_alternate_and_reach_a_winner():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    for seat, move in ((host, 0), (guest, 3), (host, 1), (guest, 4), (host, 2)):
        lobby.handle(seat, proto.message(proto.MOVE, move=move))

    final = guest_conn.last(proto.GAME_STATE)
    assert final["result"]["outcome"] == "win"
    assert final["result"]["winner_seat"] == 0
    assert host_conn.last(proto.ROOM_STATE)["players"][0]["wins"] == 1


def test_your_turn_flag_alternates_after_every_move():
    """Each ``game_state`` must be stamped per recipient, not broadcast as-is."""
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="connect4"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    assert host_conn.last(proto.GAME_STATE)["your_turn"] is True
    assert guest_conn.last(proto.GAME_STATE)["your_turn"] is False

    lobby.handle(host, proto.message(proto.MOVE, move=3))
    assert host_conn.last(proto.GAME_STATE)["your_turn"] is False
    assert guest_conn.last(proto.GAME_STATE)["your_turn"] is True

    lobby.handle(guest, proto.message(proto.MOVE, move=3))
    assert host_conn.last(proto.GAME_STATE)["your_turn"] is True
    assert guest_conn.last(proto.GAME_STATE)["your_turn"] is False


def test_spectators_never_get_the_turn_flag():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    watcher_conn, watcher = join(lobby, "watcher")
    lobby.handle(
        watcher, proto.message(proto.JOIN_ROOM, code=code, **{"as": "spectator"})
    )
    lobby.handle(host, proto.message(proto.MOVE, move=0))
    assert watcher_conn.last(proto.GAME_STATE)["your_turn"] is False


def test_nobody_has_the_turn_once_the_game_is_over():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    for seat, move in ((host, 0), (guest, 3), (host, 1), (guest, 4), (host, 2)):
        lobby.handle(seat, proto.message(proto.MOVE, move=move))
    assert host_conn.last(proto.GAME_STATE)["your_turn"] is False
    assert guest_conn.last(proto.GAME_STATE)["your_turn"] is False


def test_playing_out_of_turn_is_rejected():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="connect4"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    lobby.handle(guest, proto.message(proto.MOVE, move=0))
    assert proto.ERR_NOT_YOUR_TURN in guest_conn.errors()


def test_illegal_move_is_rejected_without_changing_the_board():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="connect4"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    lobby.handle(host, proto.message(proto.MOVE, move=99))
    assert proto.ERR_ILLEGAL_MOVE in host_conn.errors()
    room = lobby.rooms[code]
    assert room.game.empty_count == room.game.rows * room.game.cols


def test_moving_before_an_opponent_arrives_is_rejected():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    lobby.handle(host, proto.message(proto.MOVE, move=0))
    assert proto.ERR_NOT_PLAYING in host_conn.errors()


def test_third_player_becomes_a_spectator_and_cannot_move():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))

    watcher_conn, watcher = join(lobby, "watcher")
    lobby.handle(watcher, proto.message(proto.JOIN_ROOM, code=code))
    assert watcher.seat is None
    assert watcher_conn.last(proto.ROOM_STATE)["spectators"] == ["watcher"]

    lobby.handle(watcher, proto.message(proto.MOVE, move=0))
    assert proto.ERR_NOT_PLAYING in watcher_conn.errors()


def test_spectators_see_moves():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    watcher_conn, watcher = join(lobby, "watcher")
    lobby.handle(
        watcher, proto.message(proto.JOIN_ROOM, code=code, **{"as": "spectator"})
    )

    lobby.handle(host, proto.message(proto.MOVE, move=4))
    board = watcher_conn.last(proto.GAME_STATE)["board"]
    assert board["cells"][4] == int(Mark.P1)
    assert board["history"] == [4]


def test_quick_match_pairs_two_waiting_players():
    lobby = make_lobby()
    first_conn, first = join(lobby, "first")
    lobby.handle(first, proto.message(proto.QUICK_MATCH, game="connect4"))
    assert first_conn.last(proto.QUEUED)["game"] == "connect4"

    second_conn, second = join(lobby, "second")
    lobby.handle(second, proto.message(proto.QUICK_MATCH, game="connect4"))

    assert first.room_code is not None
    assert first.room_code == second.room_code
    assert {first.seat, second.seat} == {0, 1}
    assert second_conn.last(proto.GAME_STATE) is not None


def test_quick_match_queues_are_per_game():
    lobby = make_lobby()
    _, ttt = join(lobby, "ttt-player")
    lobby.handle(ttt, proto.message(proto.QUICK_MATCH, game="tictactoe"))
    _, c4 = join(lobby, "c4-player")
    lobby.handle(c4, proto.message(proto.QUICK_MATCH, game="connect4"))
    assert ttt.room_code is None and c4.room_code is None


def test_unknown_game_is_rejected():
    lobby = make_lobby()
    conn, session = join(lobby, "confused")
    lobby.handle(session, proto.message(proto.CREATE_ROOM, game="chess"))
    assert proto.ERR_UNKNOWN_GAME in conn.errors()


def test_unsupported_message_is_rejected():
    lobby = make_lobby()
    conn, session = join(lobby, "weird")
    lobby.handle(session, {"type": "self_destruct"})
    assert proto.ERR_BAD_MESSAGE in conn.errors()


def test_rematch_needs_both_players_and_swaps_marks():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    for seat, move in ((host, 0), (guest, 3), (host, 1), (guest, 4), (host, 2)):
        lobby.handle(seat, proto.message(proto.MOVE, move=move))

    room = lobby.rooms[code]
    assert room.mark_for_seat(0) is Mark.P1
    lobby.handle(host, proto.message(proto.REMATCH))
    assert room.round_number == 1  # one vote is not enough
    lobby.handle(guest, proto.message(proto.REMATCH))
    assert room.round_number == 2
    assert room.game.empty_count == 9
    assert room.mark_for_seat(0) is Mark.P2  # marks swapped for the new round


def test_rematch_is_rejected_mid_game():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    lobby.handle(host, proto.message(proto.REMATCH))
    assert proto.ERR_BAD_MESSAGE in host_conn.errors()


def test_moving_after_the_game_is_over_is_rejected():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    for seat, move in ((host, 0), (guest, 3), (host, 1), (guest, 4), (host, 2)):
        lobby.handle(seat, proto.message(proto.MOVE, move=move))
    lobby.handle(guest, proto.message(proto.MOVE, move=5))
    assert proto.ERR_GAME_OVER in guest_conn.errors()


def test_disconnect_holds_the_seat_and_token_reconnects():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="connect4"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    lobby.handle(host, proto.message(proto.MOVE, move=3))

    token = guest.token
    lobby.disconnect(guest)
    room = lobby.rooms[code]
    assert room.seats[1].reserved
    assert host_conn.last(proto.ROOM_STATE)["players"][1]["online"] is False

    back_conn, back = join(lobby, "guest")
    lobby.handle(back, proto.message(proto.HELLO, name="guest", token=token))
    assert back.seat == 1
    assert back_conn.last(proto.WELCOME)["resumed"] is True
    # The board survived the round trip.
    assert back_conn.last(proto.GAME_STATE)["board"]["history"] == [3]


def test_sweep_releases_an_abandoned_seat():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    _, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    lobby.disconnect(guest)
    assert lobby.rooms[code].seats[1].reserved

    lobby.sweep(now=lobby.rooms[code].seats[1].vacated_at + 100)
    assert not lobby.rooms[code].seats[1].reserved


def test_room_is_dropped_when_everyone_leaves():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    lobby.handle(host, proto.message(proto.LEAVE))
    assert code not in lobby.rooms


def test_chat_reaches_the_whole_room():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    lobby.handle(guest, proto.message(proto.CHAT, text="hello!"))
    expected = {"type": proto.CHAT, "from": "guest", "text": "hello!"}
    assert host_conn.last(proto.CHAT) == expected
    # The sender is part of the room too, so it echoes back to them as well.
    assert guest_conn.last(proto.CHAT) == expected


def test_list_rooms_hides_private_rooms():
    lobby = make_lobby()
    _, private = join(lobby, "hidden")
    lobby.handle(
        private, proto.message(proto.CREATE_ROOM, game="tictactoe", private=True)
    )
    public_conn, public = join(lobby, "open")
    lobby.handle(public, proto.message(proto.CREATE_ROOM, game="connect4"))
    lobby.handle(public, proto.message(proto.LIST_ROOMS))
    listed = public_conn.last(proto.ROOMS)["rooms"]
    assert [r["game"] for r in listed] == ["connect4"]


def test_room_marks_alternate_between_rounds():
    room = Room(code="TEST", game_key="tictactoe", game=create_game("tictactoe"))
    assert room.mark_for_seat(0) is Mark.P1
    assert room.seat_for_mark(Mark.P1) == 0
    room.reset_game()
    assert room.mark_for_seat(0) is Mark.P2
    assert room.seat_for_mark(Mark.P2) == 0
    assert room.seat_for_mark(Mark.P1) == 1


def test_tokens_are_never_broadcast():
    lobby = make_lobby()
    host_conn, host = join(lobby, "host")
    lobby.handle(host, proto.message(proto.CREATE_ROOM, game="tictactoe"))
    code = host_conn.last(proto.ROOM_STATE)["code"]
    guest_conn, guest = join(lobby, "guest")
    lobby.handle(guest, proto.message(proto.JOIN_ROOM, code=code))
    serialised = proto.encode(guest_conn.last(proto.ROOM_STATE))
    assert host.token not in serialised
    assert guest.token not in serialised


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
def _run_all() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failures = 0
    for name, test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - standalone runner
            failures += 1
            print(f"  ✗ {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"  ✓ {name}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
