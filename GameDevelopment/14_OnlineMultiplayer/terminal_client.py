"""Terminal client for Tic-Tac-Toe and Connect Four.

Four ways to play, all from the same board renderer::

    python terminal_client.py                                  # interactive menu
    python terminal_client.py --game c4 --mode hotseat         # two humans, one keyboard
    python terminal_client.py --game ttt --mode ai --difficulty hard
    python terminal_client.py --mode online --quick --game c4
    python terminal_client.py --mode online --room ABCD --url ws://host:8765

Online play needs :mod:`server` running somewhere reachable. While online you
can type a move, or one of the slash commands listed by ``/help``.
"""

from __future__ import annotations

import argparse
import os
import queue
import random
import sys
import threading
import time

import protocol as proto
from ai import BOT_CONFIGS, Bot, Difficulty
from boardgames import GridGame, IllegalMove, Mark, create_game, normalise_game_key
from netclient import DEFAULT_URL, ClientState, NetClient

#: ANSI escapes, blanked out by :func:`disable_colour` when not on a terminal.
COLOURS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "p1": "\033[91m",  # bright red — X / Red
    "p2": "\033[93m",  # bright yellow — O / Yellow
    "grid": "\033[90m",
    "win": "\033[42;30m",
    "info": "\033[96m",
    "warn": "\033[95m",
}


def disable_colour() -> None:
    """Replace every escape sequence with an empty string."""
    for key in COLOURS:
        COLOURS[key] = ""


def c(name: str, text: str) -> str:
    """Wrap ``text`` in the named colour."""
    return f"{COLOURS[name]}{text}{COLOURS['reset']}" if COLOURS[name] else text


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_board(game: GridGame, highlight: tuple[int, ...] = ()) -> str:
    """Draw the board with coloured marks and an optional highlighted line."""
    glyphs = game.short_marks
    width = max(1, len(glyphs[0]), len(glyphs[1]))
    winning = set(highlight)
    header = "    " + " ".join(f"{col + 1:^{width}}" for col in range(game.cols))
    lines = [c("dim", header)]
    for row in range(game.rows):
        cells = []
        for col in range(game.cols):
            index = game.index(row, col)
            mark = game.cells[index]
            if mark is Mark.EMPTY:
                cells.append(c("grid", f"{'·':^{width}}"))
            else:
                glyph = f"{glyphs[int(mark) - 1]:^{width}}"
                style = "win" if index in winning else f"p{int(mark)}"
                cells.append(c(style, glyph))
        lines.append(c("dim", f"{row + 1:>3} ") + " ".join(cells))
    return "\n".join(lines)


def status_line(game: GridGame) -> str:
    """One-line summary of whose turn it is, or how the game ended."""
    if game.winner is not None:
        name = game.mark_names[int(game.winner) - 1]
        return c("bold", f"{name} wins!")
    if game.is_draw:
        return c("bold", "Draw — board full.")
    name = game.mark_names[int(game.turn) - 1]
    return f"{c(f'p{int(game.turn)}', name)} to move."


def move_help(game: GridGame) -> str:
    """Explain how to enter a move for this game."""
    if game.key == "connect4":
        return f"Drop a disc: type a column number 1-{game.cols}."
    return (
        f"Place a mark: type a cell number 1-{game.rows * game.cols}, "
        "or a coordinate like b2."
    )


def show(game: GridGame, extra: str = "") -> None:
    """Print the board, its status line and an optional extra line."""
    highlight = game.win_cells if game.winner is not None else ()
    print()
    print(render_board(game, highlight))
    print(status_line(game))
    if extra:
        print(extra)


# ---------------------------------------------------------------------------
# Offline modes
# ---------------------------------------------------------------------------
def prompt_move(game: GridGame, who: str) -> int | None:
    """Ask the human for a move. Returns ``None`` when they want to quit."""
    while True:
        try:
            raw = input(f"{who} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw.lower() in {"q", "quit", "exit"}:
            return None
        if raw.lower() in {"?", "h", "help"}:
            print(move_help(game))
            continue
        if raw.lower() == "moves":
            print("Legal:", ", ".join(game.move_label(m) for m in game.legal_moves()))
            continue
        try:
            move = game.parse_move(raw)
        except IllegalMove as exc:
            print(c("warn", str(exc)))
            continue
        if move not in game.legal_moves():
            print(c("warn", "That move is not available."))
            continue
        return move


def play_offline(
    game: GridGame,
    bot_marks: dict[Mark, Bot],
    names: dict[Mark, str],
) -> int:
    """Run a local game. ``bot_marks`` maps a mark to the bot that plays it."""
    print(c("info", f"\n{game.title} — {move_help(game)}"))
    print(c("dim", "Type 'q' to quit, 'moves' to list legal moves."))
    while not game.is_over:
        show(game)
        mark = game.turn
        bot = bot_marks.get(mark)
        if bot is None:
            move = prompt_move(game, names[mark])
            if move is None:
                print("Goodbye.")
                return 0
        else:
            started = time.monotonic()
            move = bot.choose(game)
            elapsed = time.monotonic() - started
            print(
                c(
                    "dim",
                    f"{names[mark]} plays {game.move_label(move)} "
                    f"({game.describe_move(move)}) — {bot.nodes} nodes, "
                    f"depth {bot.depth_reached}, {elapsed:.2f}s",
                )
            )
        game.play(move)
    show(game)
    return 0


# ---------------------------------------------------------------------------
# Online mode
# ---------------------------------------------------------------------------
ONLINE_HELP = """Commands:
  <move>          play a move (a cell number, coordinate, or column)
  /chat <text>    say something to the room
  /rematch        vote for another round once this one is finished
  /rooms          list public rooms on the server
  /join <code>    join a room by code
  /quick <game>   enter the quick-match queue
  /new <game>     create a new room
  /leave          leave the current room
  /help           show this help
  /quit           disconnect and exit"""


def _stdin_reader(sink: queue.Queue) -> None:
    """Push each typed line onto ``sink`` so the main loop never blocks."""
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            sink.put(None)
            return
        sink.put(line)


def play_online(
    url: str,
    name: str,
    game_key: str,
    room_code: str | None,
    quick: bool,
    spectate: bool,
) -> int:
    """Connect to a server and play until the user quits."""
    client = NetClient(url)
    try:
        client.connect()
    except ConnectionError as exc:
        print(c("warn", str(exc)))
        print("Start a server first:  python server.py")
        return 1

    state = ClientState()
    client.send(proto.message(proto.HELLO, name=name))
    if room_code:
        client.send(
            proto.message(
                proto.JOIN_ROOM,
                code=room_code,
                **{"as": "spectator" if spectate else "player"},
            )
        )
    elif quick:
        client.send(proto.message(proto.QUICK_MATCH, game=game_key))
    else:
        client.send(proto.message(proto.CREATE_ROOM, game=game_key))

    typed: queue.Queue = queue.Queue()
    threading.Thread(target=_stdin_reader, args=(typed,), daemon=True).start()

    print(c("info", f"Connected to {url} as {name}."))
    print(c("dim", ONLINE_HELP))
    seen_log = 0
    last_render: tuple | None = None
    try:
        while True:
            for message in client.poll():
                state.apply(message)
            while seen_log < len(state.log):
                print(c("info", f"  {state.log[seen_log]}"))
                seen_log += 1

            if state.game is not None:
                signature = (
                    tuple(state.game.cells),
                    state.your_turn,
                    state.room_code,
                    state.game.winner,
                )
                if signature != last_render:
                    last_render = signature
                    _render_online(state)

            try:
                line = typed.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None or not _handle_input(client, state, line):
                break
    finally:
        client.close()
    print("Goodbye.")
    return 0


def _render_online(state: ClientState) -> None:
    """Draw the board plus the online-specific status lines."""
    game = state.game
    if game is None:
        return
    room = state.room or {}
    show(game)
    if state.is_spectator:
        print(c("dim", "You are spectating."))
    elif state.your_mark is not None:
        glyph = game.mark_names[int(state.your_mark) - 1]
        print(c("dim", f"You are {glyph} in room {room.get('code', '?')}."))
    scores = " | ".join(
        f"{p.get('name') or 'empty'} ({p.get('mark_name')}) {p.get('wins', 0)}"
        + ("" if p.get("online") else " [offline]")
        for p in room.get("players", [])
    )
    if scores:
        print(c("dim", f"Round {room.get('round', 1)} — {scores}"))
    if game.is_over:
        print(c("bold", "Type /rematch for another round."))
    elif not state.opponent_online and not state.is_spectator:
        print(c("warn", "Waiting for an opponent to join…"))
    elif state.your_turn:
        print(c("bold", "Your turn. ") + move_help(game))
    else:
        print(c("dim", "Waiting for your opponent…"))


def _handle_input(client: NetClient, state: ClientState, line: str) -> bool:
    """Act on one typed line. Returns ``False`` when the user wants to quit."""
    text = line.strip()
    if not text:
        return True
    if text.startswith("/"):
        command, _, argument = text[1:].partition(" ")
        command = command.lower()
        argument = argument.strip()
        if command in {"quit", "exit"}:
            client.send(proto.message(proto.LEAVE))
            return False
        if command == "help":
            print(c("dim", ONLINE_HELP))
        elif command == "chat":
            client.send(proto.message(proto.CHAT, text=argument))
        elif command == "rematch":
            client.send(proto.message(proto.REMATCH))
        elif command == "rooms":
            client.send(proto.message(proto.LIST_ROOMS))
        elif command == "leave":
            client.send(proto.message(proto.LEAVE))
        elif command == "join" and argument:
            client.send(proto.message(proto.JOIN_ROOM, code=argument.upper()))
        elif command in {"quick", "new"}:
            try:
                key = normalise_game_key(argument or "tictactoe")
            except KeyError:
                print(c("warn", f"Unknown game {argument!r}. Try ttt or c4."))
                return True
            kind = proto.QUICK_MATCH if command == "quick" else proto.CREATE_ROOM
            client.send(proto.message(kind, game=key))
        else:
            print(c("warn", f"Unknown command /{command}. Try /help."))
        return True

    if state.game is None:
        print(c("warn", "No game in progress yet."))
        return True
    try:
        move = state.game.parse_move(text)
    except IllegalMove as exc:
        print(c("warn", str(exc)))
        return True
    client.send(proto.message(proto.MOVE, move=move))
    return True


# ---------------------------------------------------------------------------
# Menu + CLI
# ---------------------------------------------------------------------------
def choose(prompt: str, options: list[tuple[str, str]], default: int = 0) -> str:
    """Print a numbered menu and return the chosen option's key."""
    print(c("bold", f"\n{prompt}"))
    for index, (_, label) in enumerate(options, start=1):
        marker = " (default)" if index - 1 == default else ""
        print(f"  {index}. {label}{marker}")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)
        if not raw:
            return options[default][0]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        for key, _ in options:
            if raw.lower() == key:
                return key
        print(c("warn", "Pick one of the listed numbers."))


def interactive_menu(args: argparse.Namespace) -> argparse.Namespace:
    """Fill in ``game``/``mode`` and friends by asking the user."""
    print(c("bold", "\n=== Online Multiplayer Board Games ==="))
    args.game = choose(
        "Which game?",
        [("tictactoe", "Tic-Tac-Toe (3x3)"), ("connect4", "Connect Four (7x6)")],
    )
    args.mode = choose(
        "How do you want to play?",
        [
            ("ai", "Against the computer"),
            ("hotseat", "Two players on this keyboard"),
            ("online", "Online against another machine"),
        ],
    )
    if args.mode == "ai":
        args.difficulty = choose(
            "Bot strength?",
            [
                ("medium", "Medium — searches a few moves ahead"),
                ("easy", "Easy — blunders sometimes"),
                ("hard", "Hard — perfect at Tic-Tac-Toe"),
            ],
        )
        args.side = choose(
            "Who moves first?", [("first", "You do"), ("second", "The computer does")]
        )
    elif args.mode == "online":
        how = choose(
            "Find a game how?",
            [
                ("quick", "Quick match against whoever is waiting"),
                ("new", "Create a room and share the code"),
                ("join", "Join a room by code"),
            ],
        )
        args.quick = how == "quick"
        if how == "join":
            args.room = input("Room code > ").strip().upper()
        url = input(f"Server URL [{args.url}] > ").strip()
        if url:
            args.url = url
    return args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Terminal client for Tic-Tac-Toe and Connect Four",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--game",
        default=None,
        help="tictactoe/ttt or connect4/c4 (default: ask)",
    )
    parser.add_argument(
        "--mode",
        choices=["hotseat", "ai", "online"],
        default=None,
        help="hotseat, ai, or online (default: ask)",
    )
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty],
        default=Difficulty.MEDIUM.value,
        help="bot strength for --mode ai",
    )
    parser.add_argument(
        "--side",
        choices=["first", "second"],
        default="first",
        help="whether you move first against the bot",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="server WebSocket URL")
    parser.add_argument("--room", default=None, help="room code to join")
    parser.add_argument(
        "--quick", action="store_true", help="use the matchmaking queue"
    )
    parser.add_argument(
        "--spectate", action="store_true", help="join the room as a spectator"
    )
    parser.add_argument(
        "--name",
        default=os.environ.get("USER") or os.environ.get("USERNAME") or "player",
        help="display name shown to other players",
    )
    parser.add_argument("--seed", type=int, default=None, help="seed the bot's RNG")
    parser.add_argument(
        "--no-color", action="store_true", help="disable ANSI colour output"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.no_color or not sys.stdout.isatty():
        disable_colour()
    if args.mode is None or args.game is None:
        if args.room and args.mode is None:
            args.mode = "online"
        if args.mode is None or args.game is None:
            args = interactive_menu(args)

    try:
        game_key = normalise_game_key(args.game or "tictactoe")
    except KeyError:
        print(c("warn", f"Unknown game {args.game!r}. Try ttt or c4."))
        return 2

    if args.mode == "online":
        return play_online(
            args.url,
            args.name,
            game_key,
            args.room,
            args.quick,
            args.spectate,
        )

    game = create_game(game_key)
    rng = random.Random(args.seed) if args.seed is not None else None
    names = {Mark.P1: game.mark_names[0], Mark.P2: game.mark_names[1]}
    bots: dict[Mark, Bot] = {}
    if args.mode == "ai":
        bot_mark = Mark.P2 if args.side == "first" else Mark.P1
        bots[bot_mark] = Bot(args.difficulty, rng=rng)
        names[bot_mark] = f"Computer ({args.difficulty})"
        names[bot_mark.other] = "You"
        budget = BOT_CONFIGS[Difficulty(args.difficulty)]
        print(
            c(
                "dim",
                f"Bot budget: depth {budget.max_depth}, {budget.time_limit:.2f}s"
                f", blunder rate {budget.blunder_rate:.0%}",
            )
        )
    return play_offline(game, bots, names)


if __name__ == "__main__":
    raise SystemExit(main())
