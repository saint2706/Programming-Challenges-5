# Online Multiplayer Tic-Tac-Toe & Connect-4

Both games, over the network, with a Pygame client **and** a terminal client.
A WebSocket server owns the authoritative board; clients render it and send
moves. Offline you get hot-seat play and a negamax bot, so nothing here needs a
second human to try out.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)
- [Wire Protocol](#wire-protocol)
- [Assets](#assets)
- [Testing](#testing)

## ✨ Features

- **Two games, one rule engine.** Tic-Tac-Toe and Connect Four are both
  _n-in-a-row on a grid_, so `boardgames.py` implements the board, turn order and
  win detection once. Tic-Tac-Toe generalises to any square size and win length;
  Connect Four to any rows × columns.
- **Authoritative server.** `server.py` + `lobby.py` validate every move: wrong
  turn, occupied cell, full column, spectator, and post-game moves are all
  rejected with a specific error code. Clients never decide the outcome.
- **Named rooms, quick match and spectators.** Create a room and share a
  four-character code, or drop into the per-game matchmaking queue. Extra joiners
  become spectators and see moves live.
- **Reconnect without losing the game.** Each session gets a token; if your
  connection drops the seat is held (default 2 minutes) and re-sending the token
  in `hello` puts you back in the same room with the board intact.
- **Rematches with alternating first move.** Both players vote, marks swap, and
  the win/draw tally carries across rounds.
- **A bot that plays properly.** Negamax with alpha-beta, iterative deepening,
  a bound-flagged transposition table and centre-first move ordering. At `hard`
  the Tic-Tac-Toe tree is searched exhaustively, so the bot never loses.
- **Two front-ends, same state.** `gui_client.py` (Pygame, CC0 Kenney art and
  sound) and `terminal_client.py` (ANSI colour, slash commands) both consume the
  same `ClientState`.

## 🏗️ Architecture

```
boardgames.py      Rules only: GridGame base, TicTacToe, ConnectFour  (no deps)
 ├─ Mark            EMPTY / P1 / P2
 ├─ GridGame        board, turns, n-in-a-row detection, undo, (de)serialisation
 ├─ TicTacToe       move = cell index
 └─ ConnectFour     move = column; discs stack

ai.py              Negamax + alpha-beta + TT + iterative deepening
protocol.py        Message vocabulary, encode/decode, field validation
lobby.py           Rooms, seats, matchmaking, reconnect — transport-agnostic
server.py          WebSocket adapter around Lobby (the only asyncio in the tree)
netclient.py       Threaded client socket + ClientState folding of server frames
terminal_client.py ANSI front-end: hotseat / vs bot / online
gui_client.py      Pygame front-end: menu, board, sidebar, online message pump
fetch_assets.py    Downloads the CC0 Kenney assets used by the GUI
assets/            Committed sprites, fonts and sound effects (+ CREDITS.md)
```

Headless tests (no pygame, no sockets) live in
`tests/GameDevelopment/test_14_online_multiplayer.py`.

`boardgames.py`, `ai.py`, `protocol.py` and `lobby.py` import nothing beyond the
standard library — that is what lets the whole multiplayer flow be tested without
a display or a socket.

## 💻 Installation

The rules, bot, protocol, lobby and tests are pure standard-library Python
(3.10+). The two front-ends add one dependency each:

```bash
pip install websockets   # server + online play (already in requirements.txt)
pip install pygame       # graphical client only
cd GameDevelopment/14_OnlineMultiplayer
```

The art and audio are committed, so nothing needs downloading. To refresh them
from source:

```bash
python fetch_assets.py --force
```

## 🚀 Usage

### Graphical client

```bash
python gui_client.py                                  # menu: pick game + mode
python gui_client.py --game c4 --mode ai --difficulty hard
python gui_client.py --mode online --quick            # quick match
python gui_client.py --mode online --room ABCD --url ws://192.168.1.5:8765
```

### Terminal client

```bash
python terminal_client.py                             # interactive menu
python terminal_client.py --game ttt --mode ai --difficulty hard
python terminal_client.py --game c4 --mode hotseat
python terminal_client.py --mode online --quick --game c4
python terminal_client.py --mode online --room ABCD --url ws://host:8765
```

```
    1 2 3 4 5 6 7
  1 · · · · · · ·
  2 · · · · · · ·
  3 · · · · · · ·
  4 · · · B · · ·
  5 · · · R · · ·
  6 · · · R · · B
Red to move.
```

### Server

```bash
python server.py                        # ws://127.0.0.1:8765
python server.py --host 0.0.0.0 --port 8765 --verbose
python server.py --reconnect-grace 300  # hold dropped seats for 5 minutes
```

A full two-machine session: run `server.py` on one host, then point both clients
at it with `--url ws://<host>:8765` — one with `--mode online --quick`, the other
the same, and the matchmaker pairs them.

## 🎮 Controls

### Graphical client

| Action                     | Control                                                  |
| :------------------------- | :------------------------------------------------------- |
| **Place mark / drop disc** | Left click a cell (Tic-Tac-Toe) or column (Connect Four) |
| **Menu buttons**           | Left click                                               |
| **Type server URL / code** | Click the field, then type                               |
| **Back to menu**           | ESC                                                      |
| **Quit**                   | ESC from the menu, or close the window                   |

A translucent ghost piece previews where your move lands, and Connect Four adds
a drop arrow above the hovered column.

### Terminal client

| Input                          | Effect                                                     |
| :----------------------------- | :--------------------------------------------------------- |
| `5`                            | Tic-Tac-Toe: play cell 5 (numbered left→right, top→bottom) |
| `b2`                           | Tic-Tac-Toe: play column b, row 2                          |
| `4`                            | Connect Four: drop into column 4                           |
| `moves`                        | List every legal move                                      |
| `q`                            | Quit an offline game                                       |
| `/chat <text>`                 | Talk to the room (online)                                  |
| `/rematch`                     | Vote for another round (online)                            |
| `/rooms`, `/join <code>`       | List public rooms, join one (online)                       |
| `/quick <game>`, `/new <game>` | Queue for a match, or open a new room (online)             |
| `/leave`, `/quit`              | Leave the room, or disconnect and exit                     |

## 📡 Wire Protocol

Every frame is one JSON object with a `type`. Client frames: `hello`,
`create_room`, `join_room`, `quick_match`, `cancel_match`, `list_rooms`, `move`,
`rematch`, `chat`, `leave`, `ping`. Server frames: `welcome`, `room_state`,
`game_state`, `queued`, `rooms`, `chat`, `notice`, `error`, `pong`.

```jsonc
// client -> server
{ "type": "hello", "name": "ada", "token": "optional-resume-token" }
{ "type": "move", "move": 3 }

// server -> client (game_state is stamped per recipient)
{
  "type": "game_state",
  "code": "K7QF",
  "your_turn": true,
  "board": {
    "game": "connect4", "rows": 6, "cols": 7, "connect": 4,
    "cells": [0, 0, 1, 2, ...], "turn": 1,
    "winner": null, "win_cells": [], "history": [3, 3, 4],
    "legal_moves": [0, 1, 2, 3, 4, 5, 6], "over": false, "draw": false
  }
}
```

Two details worth knowing:

- `your_turn` is per-connection, so the board frame is built once and stamped
  individually rather than broadcast verbatim.
- Clients rebuild the board by **replaying `history`** through the same rules
  module the server uses, so a tampered `cells` array cannot push a client into
  an impossible position.

Error frames carry a machine-readable `code`: `bad_message`, `no_room`,
`not_playing`, `not_your_turn`, `illegal_move`, `unknown_game`, `game_over`.

## 🎨 Assets

All art, fonts and sound are **CC0** (public domain) by
[Kenney](https://kenney.nl/assets): the Game Icons, Input Prompts, Boardgame Pack,
Kenney Fonts and UI Audio packs. `fetch_assets.py` resolves each pack's current
download URL, caches the ZIP under `.asset-cache/` (git-ignored) and extracts only
the dozen files the game needs. See [assets/CREDITS.md](assets/CREDITS.md) for the
per-file mapping. If `assets/` is missing the GUI still runs, drawing vector
placeholder pieces and warning in the corner.

## 🧪 Testing

61 headless tests cover the rules, the bot, the protocol and the lobby —
no display and no sockets required:

```bash
python tests/GameDevelopment/test_14_online_multiplayer.py  # standalone runner with tick-marks
# or
python -m pytest tests/GameDevelopment/test_14_online_multiplayer.py
```

Highlights: Connect Four's stacking/undo, a full-board draw, the bot never losing
Tic-Tac-Toe across seeded games from both sides, illegal-move and out-of-turn
rejection, spectators being read-only, quick-match pairing, mark-swapping
rematches, token reconnect restoring the board, and the assertion that session
tokens never appear in a broadcast frame.
