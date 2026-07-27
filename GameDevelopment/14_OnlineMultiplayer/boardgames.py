"""Board game rules for Tic-Tac-Toe and Connect Four.

Both games are *n-in-a-row on a rectangular grid*, so they share a single
:class:`GridGame` base that owns the board, turn order, win detection and
(de)serialisation. The subclasses only describe how a move maps to a cell:

* :class:`TicTacToe` — a move names the cell directly.
* :class:`ConnectFour` — a move names a column and the disc falls to the
  lowest empty row.

This module is deliberately free of any networking, rendering or AI code so
that the rules can be unit-tested headlessly and reused by the server, the
terminal client and the Pygame client alike.
"""

from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, Iterator, Sequence

#: The four line directions to probe for a win: E, S, SE, SW.
_DIRECTIONS: tuple[tuple[int, int], ...] = ((1, 0), (0, 1), (1, 1), (-1, 1))


class Mark(IntEnum):
    """Occupant of a board cell."""

    EMPTY = 0
    P1 = 1
    P2 = 2

    @property
    def other(self) -> "Mark":
        """The opposing mark (``EMPTY`` is its own opposite)."""
        if self is Mark.P1:
            return Mark.P2
        if self is Mark.P2:
            return Mark.P1
        return Mark.EMPTY


class IllegalMove(ValueError):
    """Raised when a move is not available in the current position."""


class GridGame:
    """Shared implementation of an *n-in-a-row* game on a ``rows x cols`` grid.

    Subclasses set :attr:`key`, :attr:`title` and implement :meth:`legal_moves`
    plus :meth:`_cell_for_move`.
    """

    key: ClassVar[str] = "grid"
    title: ClassVar[str] = "Grid Game"
    #: Human-readable name for each player's mark, indexed by ``Mark``.
    mark_names: ClassVar[tuple[str, str]] = ("P1", "P2")
    #: Single-character glyphs for compact board rendering.
    short_marks: ClassVar[tuple[str, str]] = ("1", "2")

    def __init__(self, rows: int, cols: int, connect: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("board must have at least one row and column")
        if connect < 2:
            raise ValueError("connect length must be at least 2")
        self.rows = rows
        self.cols = cols
        self.connect = connect
        self.cells: list[Mark] = [Mark.EMPTY] * (rows * cols)
        self.turn: Mark = Mark.P1
        self.winner: Mark | None = None
        self.win_cells: tuple[int, ...] = ()
        #: Moves played so far, oldest first (enables :meth:`undo`).
        self.history: list[int] = []

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def index(self, row: int, col: int) -> int:
        """Flat index of ``(row, col)``."""
        return row * self.cols + col

    def coords(self, index: int) -> tuple[int, int]:
        """``(row, col)`` of a flat index."""
        return divmod(index, self.cols)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def at(self, row: int, col: int) -> Mark:
        return self.cells[self.index(row, col)]

    def rows_of_cells(self) -> list[list[Mark]]:
        """The board as a list of rows, top row first."""
        return [
            self.cells[r * self.cols : (r + 1) * self.cols] for r in range(self.rows)
        ]

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    @property
    def is_over(self) -> bool:
        return self.winner is not None or not self.legal_moves()

    @property
    def is_draw(self) -> bool:
        return self.winner is None and not self.legal_moves()

    def legal_moves(self) -> list[int]:  # pragma: no cover - overridden
        raise NotImplementedError

    def _cell_for_move(self, move: int) -> int:  # pragma: no cover - overridden
        """Flat index the disc/mark ends up in for ``move``."""
        raise NotImplementedError

    def cell_for_move(self, move: int) -> int:
        """Public view of :meth:`_cell_for_move` for callers outside the class."""
        return self._cell_for_move(move)

    @property
    def empty_count(self) -> int:
        """How many cells are still unoccupied."""
        return sum(1 for c in self.cells if c is Mark.EMPTY)

    def play(self, move: int) -> int:
        """Apply ``move`` for the player to move and return the filled cell.

        Raises :class:`IllegalMove` if the game is finished or the move is not
        currently legal.
        """
        if self.winner is not None:
            raise IllegalMove("game is already decided")
        if move not in self.legal_moves():
            raise IllegalMove(f"move {move!r} is not legal")
        cell = self._cell_for_move(move)
        self.cells[cell] = self.turn
        self.history.append(move)
        if self._is_winning_cell(cell):
            self.winner = self.turn
        else:
            self.turn = self.turn.other
        return cell

    def undo(self) -> None:
        """Undo the most recent move (used by the search in :mod:`ai`)."""
        if not self.history:
            raise IllegalMove("nothing to undo")
        move = self.history.pop()
        cell = self._undo_cell(move)
        mover = self.cells[cell]
        self.cells[cell] = Mark.EMPTY
        self.turn = mover
        self.winner = None
        self.win_cells = ()

    def _undo_cell(self, move: int) -> int:
        """Cell that ``move`` filled, given the board *after* the move."""
        return self._cell_for_move(move)

    def _is_winning_cell(self, cell: int) -> bool:
        """Whether the mark at ``cell`` completes a line, recording it."""
        mark = self.cells[cell]
        if mark is Mark.EMPTY:
            return False
        row, col = self.coords(cell)
        for dc, dr in _DIRECTIONS:
            line = [cell]
            for sign in (1, -1):
                r, c = row + dr * sign, col + dc * sign
                while self.in_bounds(r, c) and self.at(r, c) is mark:
                    line.append(self.index(r, c))
                    r, c = r + dr * sign, c + dc * sign
            if len(line) >= self.connect:
                self.win_cells = tuple(sorted(line))
                return True
        return False

    def winning_line_for(self, mark: Mark) -> tuple[int, ...]:
        """Any completed line owned by ``mark``, or ``()`` if there is none."""
        for cell, occupant in enumerate(self.cells):
            if occupant is not mark:
                continue
            saved = self.win_cells
            if self._is_winning_cell(cell):
                line = self.win_cells
                self.win_cells = saved
                return line
            self.win_cells = saved
        return ()

    def open_windows(self, mark: Mark) -> Iterator[tuple[int, ...]]:
        """Yield every ``connect``-length window that ``mark`` could still win.

        A window qualifies when it contains no opposing mark. Used by the AI
        evaluation function.
        """
        opponent = mark.other
        for row in range(self.rows):
            for col in range(self.cols):
                for dc, dr in _DIRECTIONS:
                    end_r = row + dr * (self.connect - 1)
                    end_c = col + dc * (self.connect - 1)
                    if not self.in_bounds(end_r, end_c):
                        continue
                    window = tuple(
                        self.index(row + dr * i, col + dc * i)
                        for i in range(self.connect)
                    )
                    if any(self.cells[i] is opponent for i in window):
                        continue
                    yield window

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """JSON-friendly snapshot, round-trippable via :meth:`from_dict`."""
        return {
            "game": self.key,
            "rows": self.rows,
            "cols": self.cols,
            "connect": self.connect,
            "cells": [int(c) for c in self.cells],
            "turn": int(self.turn),
            "winner": int(self.winner) if self.winner is not None else None,
            "win_cells": list(self.win_cells),
            "history": list(self.history),
            "legal_moves": self.legal_moves(),
            "over": self.is_over,
            "draw": self.is_draw,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GridGame":
        """Rebuild a game from :meth:`to_dict` output by replaying its history."""
        game = create_game(
            data["game"],
            rows=data.get("rows"),
            cols=data.get("cols"),
            connect=data.get("connect"),
        )
        for move in data.get("history", []):
            game.play(move)
        return game

    def copy(self) -> "GridGame":
        """A deep copy that shares no mutable state with ``self``."""
        clone = create_game(
            self.key, rows=self.rows, cols=self.cols, connect=self.connect
        )
        clone.cells = list(self.cells)
        clone.turn = self.turn
        clone.winner = self.winner
        clone.win_cells = self.win_cells
        clone.history = list(self.history)
        return clone

    def position_key(self) -> tuple:
        """Hashable key for transposition tables."""
        return (bytes(int(c) for c in self.cells), int(self.turn))

    # ------------------------------------------------------------------
    # Presentation helpers (used by both front-ends)
    # ------------------------------------------------------------------
    def move_label(self, move: int) -> str:
        """Short label a human would type for ``move``."""
        return str(move)

    def parse_move(self, text: str) -> int:
        """Parse a human-entered move label. Raises :class:`IllegalMove`."""
        try:
            return int(text.strip())
        except ValueError as exc:
            raise IllegalMove(f"cannot parse move {text!r}") from exc

    def describe_move(self, move: int) -> str:
        row, col = self.coords(self._cell_for_move(move))
        return f"row {row + 1}, column {col + 1}"


class TicTacToe(GridGame):
    """Tic-Tac-Toe, generalised to any square board and win length.

    Moves are flat cell indices, numbered left-to-right, top-to-bottom.
    """

    key = "tictactoe"
    title = "Tic-Tac-Toe"
    mark_names = ("X", "O")
    short_marks = ("X", "O")

    def __init__(self, size: int = 3, connect: int = 3) -> None:
        super().__init__(rows=size, cols=size, connect=connect)

    @property
    def size(self) -> int:
        return self.rows

    def legal_moves(self) -> list[int]:
        if self.winner is not None:
            return []
        return [i for i, c in enumerate(self.cells) if c is Mark.EMPTY]

    def _cell_for_move(self, move: int) -> int:
        return move

    def move_label(self, move: int) -> str:
        """1-based cell number, matching what the boards print."""
        return str(move + 1)

    def parse_move(self, text: str) -> int:
        """Accept ``5`` (cell number) or ``b2`` / ``2b`` (column+row)."""
        raw = text.strip().lower().replace(",", " ").replace(" ", "")
        if not raw:
            raise IllegalMove("empty move")
        if raw.isdigit():
            return int(raw) - 1
        letters = [ch for ch in raw if ch.isalpha()]
        digits = [ch for ch in raw if ch.isdigit()]
        if len(letters) == 1 and len(digits) == 1:
            col = ord(letters[0]) - ord("a")
            row = int(digits[0]) - 1
            if self.in_bounds(row, col):
                return self.index(row, col)
        raise IllegalMove(f"cannot parse move {text!r}")

    def describe_move(self, move: int) -> str:
        row, col = self.coords(move)
        return f"{chr(ord('a') + col)}{row + 1}"


class ConnectFour(GridGame):
    """Connect Four: drop a disc into a column and it lands on the stack.

    Moves are 0-based column indices.
    """

    key = "connect4"
    title = "Connect Four"
    mark_names = ("Red", "Blue")
    short_marks = ("R", "B")

    def __init__(self, rows: int = 6, cols: int = 7, connect: int = 4) -> None:
        super().__init__(rows=rows, cols=cols, connect=connect)

    def column_height(self, col: int) -> int:
        """Number of discs already stacked in ``col``."""
        height = 0
        for row in range(self.rows - 1, -1, -1):
            if self.at(row, col) is Mark.EMPTY:
                break
            height += 1
        return height

    def landing_row(self, col: int) -> int | None:
        """Row a disc dropped into ``col`` would occupy, or ``None`` if full."""
        for row in range(self.rows - 1, -1, -1):
            if self.at(row, col) is Mark.EMPTY:
                return row
        return None

    def legal_moves(self) -> list[int]:
        if self.winner is not None:
            return []
        return [c for c in range(self.cols) if self.landing_row(c) is not None]

    def _cell_for_move(self, move: int) -> int:
        if not 0 <= move < self.cols:
            raise IllegalMove(f"column {move} is off the board")
        row = self.landing_row(move)
        if row is None:
            raise IllegalMove(f"column {move} is full")
        return self.index(row, move)

    def _undo_cell(self, move: int) -> int:
        """Topmost occupied cell of the column, i.e. the disc just dropped."""
        for row in range(self.rows):
            if self.at(row, move) is not Mark.EMPTY:
                return self.index(row, move)
        raise IllegalMove(f"column {move} is empty")

    def move_label(self, move: int) -> str:
        """1-based column number, matching the printed column headers."""
        return str(move + 1)

    def parse_move(self, text: str) -> int:
        raw = text.strip().lower()
        if raw.isdigit():
            return int(raw) - 1
        if len(raw) == 1 and raw.isalpha():
            return ord(raw) - ord("a")
        raise IllegalMove(f"cannot parse column {text!r}")

    def describe_move(self, move: int) -> str:
        return f"column {move + 1}"


#: Registry of playable games, keyed by their wire identifier.
GAMES: dict[str, type[GridGame]] = {
    TicTacToe.key: TicTacToe,
    ConnectFour.key: ConnectFour,
}

#: Aliases accepted on the command line and in protocol messages.
GAME_ALIASES: dict[str, str] = {
    "tictactoe": TicTacToe.key,
    "tic-tac-toe": TicTacToe.key,
    "ttt": TicTacToe.key,
    "t3": TicTacToe.key,
    "connect4": ConnectFour.key,
    "connect-4": ConnectFour.key,
    "connectfour": ConnectFour.key,
    "c4": ConnectFour.key,
}


def normalise_game_key(name: str) -> str:
    """Map a user-supplied game name onto a registry key."""
    key = GAME_ALIASES.get(name.strip().lower())
    if key is None:
        raise KeyError(f"unknown game {name!r}")
    return key


def create_game(
    name: str,
    rows: int | None = None,
    cols: int | None = None,
    connect: int | None = None,
) -> GridGame:
    """Instantiate a registered game, optionally overriding its dimensions."""
    key = normalise_game_key(name)
    cls = GAMES[key]
    if rows is None and cols is None and connect is None:
        return cls()
    if cls is TicTacToe:
        size = rows or cols or 3
        return TicTacToe(size=size, connect=connect or min(3, size))
    return ConnectFour(rows=rows or 6, cols=cols or 7, connect=connect or 4)


def render_ascii(
    game: GridGame,
    marks: Sequence[str] | None = None,
    highlight: Sequence[int] | None = None,
) -> str:
    """Render ``game`` as a plain-text board (no ANSI codes).

    ``marks`` overrides the two player glyphs (the compact
    :attr:`GridGame.short_marks` by default); ``highlight`` wraps the given
    cells in brackets, which the terminal client uses to show a winning line.
    """
    glyphs = tuple(marks or game.short_marks)
    highlighted = set(highlight or ())
    width = max(1, len(glyphs[0]), len(glyphs[1]))
    lines = ["   " + "".join(f" {c + 1:^{width}} " for c in range(game.cols))]
    for r in range(game.rows):
        cells = []
        for c in range(game.cols):
            i = game.index(r, c)
            mark = game.cells[i]
            glyph = f"{'.' if mark is Mark.EMPTY else glyphs[int(mark) - 1]:^{width}}"
            cells.append(f"[{glyph}]" if i in highlighted else f" {glyph} ")
        lines.append(f"{r + 1:>2} " + "".join(cells))
    return "\n".join(lines)
