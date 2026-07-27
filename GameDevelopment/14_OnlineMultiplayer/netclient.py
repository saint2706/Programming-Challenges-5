"""Client-side networking and state tracking, shared by both front-ends.

:class:`NetClient` wraps ``websockets``' synchronous client in a reader thread
and exposes a poll-based API, which suits a Pygame frame loop and a terminal
REPL equally well. :class:`ClientState` folds incoming frames into the handful
of values a UI actually needs to draw (board, whose turn, roster, log), so the
message vocabulary is interpreted in exactly one place.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Any

import protocol as proto
from boardgames import GridGame, Mark, create_game

DEFAULT_URL = "ws://127.0.0.1:8765"


class NetClient:
    """A background-thread WebSocket client with a non-blocking inbox."""

    def __init__(self, url: str = DEFAULT_URL) -> None:
        self.url = url
        self.inbox: queue.Queue[dict[str, Any]] = queue.Queue()
        self._socket: Any = None
        self._thread: threading.Thread | None = None
        self._closing = False
        #: Last transport-level failure, if any.
        self.error: str | None = None

    @property
    def connected(self) -> bool:
        return self._socket is not None and not self._closing

    def connect(self, timeout: float = 5.0) -> None:
        """Open the connection and start the reader thread.

        Raises :class:`ConnectionError` when the server cannot be reached, so
        callers can show a message instead of hanging.
        """
        try:
            from websockets.sync.client import connect as ws_connect
        except ImportError as exc:  # pragma: no cover - depends on install
            raise ConnectionError(
                "the 'websockets' package (>=12) is required for online play"
            ) from exc
        try:
            self._socket = ws_connect(self.url, open_timeout=timeout)
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            raise ConnectionError(f"cannot connect to {self.url}: {exc}") from exc
        self._closing = False
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self) -> None:
        socket = self._socket
        try:
            for raw in socket:
                try:
                    self.inbox.put(proto.decode(raw))
                except proto.ProtocolError as exc:
                    self.inbox.put(proto.error(proto.ERR_BAD_MESSAGE, str(exc)))
        except Exception as exc:  # pragma: no cover - transport specific
            if not self._closing:
                self.error = f"{type(exc).__name__}: {exc}"
                self.inbox.put(proto.error("disconnected", str(exc)))
        finally:
            self.inbox.put(proto.notice("Connection closed."))

    def send(self, message: dict[str, Any]) -> None:
        """Send one message; failures are reported through :attr:`error`."""
        if self._socket is None:
            self.error = "not connected"
            return
        try:
            self._socket.send(proto.encode(message))
        except Exception as exc:  # pragma: no cover - transport specific
            self.error = f"{type(exc).__name__}: {exc}"

    def poll(self, limit: int = 64) -> list[dict[str, Any]]:
        """Drain up to ``limit`` pending messages without blocking."""
        messages = []
        for _ in range(limit):
            try:
                messages.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return messages

    def close(self) -> None:
        """Close the socket and stop the reader thread."""
        self._closing = True
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:  # pragma: no cover - transport specific
                pass
            self._socket = None


@dataclass
class ClientState:
    """Everything a UI needs to render, folded from server frames."""

    player_id: str | None = None
    token: str | None = None
    server_name: str | None = None
    room: dict[str, Any] | None = None
    game: GridGame | None = None
    seat: int | None = None
    your_mark: Mark | None = None
    your_turn: bool = False
    result: dict[str, Any] | None = None
    queued_for: str | None = None
    rooms: list[dict[str, Any]] = field(default_factory=list)
    #: Human-readable feed of notices, chat and errors (most recent last).
    log: list[str] = field(default_factory=list)
    last_error: str | None = None

    @property
    def in_room(self) -> bool:
        return self.room is not None

    @property
    def room_code(self) -> str | None:
        return None if self.room is None else self.room.get("code")

    @property
    def is_spectator(self) -> bool:
        return self.in_room and self.seat is None

    @property
    def opponent_online(self) -> bool:
        """Whether the other seat currently has a connected player."""
        if self.room is None or self.seat is None:
            return False
        return any(
            p.get("online")
            for p in self.room.get("players", [])
            if p["seat"] != self.seat
        )

    def note(self, text: str, limit: int = 200) -> None:
        """Append ``text`` to the log, trimming the oldest entries."""
        self.log.append(text)
        del self.log[:-limit]

    def apply(self, message: dict[str, Any]) -> str:
        """Fold one server frame into the state and return its ``type``."""
        kind = message.get("type", "")
        if kind == proto.WELCOME:
            self.player_id = message.get("player_id")
            self.token = message.get("token")
            self.server_name = message.get("server")
            if message.get("resumed"):
                self.note("Resumed your previous session.")
        elif kind == proto.ROOM_STATE:
            self.room = message
            self.seat = message.get("seat")
            mark = message.get("your_mark")
            self.your_mark = Mark(mark) if mark else None
            self.queued_for = None
        elif kind == proto.GAME_STATE:
            board = message.get("board") or {}
            self.game = _rebuild(board)
            self.your_turn = bool(message.get("your_turn"))
            self.result = message.get("result")
        elif kind == proto.QUEUED:
            self.queued_for = message.get("game")
            self.note(f"Queued for {self.queued_for} — waiting for an opponent.")
        elif kind == proto.ROOMS:
            self.rooms = list(message.get("rooms", []))
        elif kind == proto.CHAT:
            self.note(f"{message.get('from', '?')}: {message.get('text', '')}")
        elif kind == proto.NOTICE:
            self.note(str(message.get("text", "")))
        elif kind == proto.ERROR:
            self.last_error = str(message.get("text", "error"))
            self.note(f"! {self.last_error}")
        return kind


def _rebuild(board: dict[str, Any]) -> GridGame:
    """Rebuild a game from a ``game_state`` board payload.

    Replaying the move history keeps client and server rules identical: a
    tampered ``cells`` array cannot put the client into an impossible position.
    """
    game = create_game(
        board.get("game", "tictactoe"),
        rows=board.get("rows"),
        cols=board.get("cols"),
        connect=board.get("connect"),
    )
    for move in board.get("history", []):
        game.play(move)
    return game
