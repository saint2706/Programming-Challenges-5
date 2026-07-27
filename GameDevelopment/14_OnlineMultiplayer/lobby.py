"""Rooms, matchmaking and turn arbitration — with no networking in sight.

:class:`Lobby` is a synchronous state machine. It receives already-decoded
message dicts and pushes replies through a ``send(dict)`` callable on each
connection, which is all :mod:`server` has to supply. Keeping the transport out
means the whole multiplayer flow — create/join, quick match, illegal-move
rejection, spectators, reconnect, rematch — is unit-testable without opening a
socket.
"""

from __future__ import annotations

import random
import string
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import protocol as proto
from boardgames import (
    GAMES,
    GridGame,
    IllegalMove,
    Mark,
    create_game,
    normalise_game_key,
)

#: Characters used for room codes: unambiguous when read aloud.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 4
#: Seconds a disconnected player's seat is held open for a reconnect.
DEFAULT_RECONNECT_GRACE = 120.0


def _new_code(taken: Iterable[str], rng: random.Random) -> str:
    """A short room code not already in ``taken``."""
    existing = set(taken)
    for _ in range(1000):
        code = "".join(rng.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if code not in existing:
            return code
    # Fall back to a longer code rather than loop forever.
    return "".join(rng.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH + 4))


@dataclass
class Session:
    """One connected client.

    A session owns the *token* that lets the same human reclaim their seat after
    a dropped connection, so tokens are never broadcast to other players.
    """

    id: str
    send: Callable[[dict[str, Any]], None]
    token: str
    name: str = "anonymous"
    room_code: str | None = None
    #: ``0``/``1`` when seated as a player, ``None`` when spectating.
    seat: int | None = None
    connected: bool = True

    @property
    def is_player(self) -> bool:
        return self.seat is not None

    def deliver(self, message: dict[str, Any]) -> None:
        """Send ``message``, ignoring failures from an already-dead transport."""
        if not self.connected:
            return
        try:
            self.send(message)
        except Exception:  # pragma: no cover - transport specific
            self.connected = False


@dataclass
class Seat:
    """A player slot in a room."""

    session: Session | None = None
    name: str = ""
    token: str = ""
    #: When the seat's occupant dropped, or ``None`` while they are connected.
    vacated_at: float | None = None
    wins: int = 0

    @property
    def occupied(self) -> bool:
        return self.session is not None and self.session.connected

    @property
    def reserved(self) -> bool:
        """True when the seat is empty but still held for a reconnect."""
        return self.session is None and bool(self.token)


@dataclass
class Room:
    """A single match: two seats, any number of spectators, one live game."""

    code: str
    game_key: str
    game: GridGame
    private: bool = False
    seats: tuple[Seat, Seat] = field(default_factory=lambda: (Seat(), Seat()))
    spectators: list[Session] = field(default_factory=list)
    #: Seat indices that have asked for a rematch.
    rematch_votes: set[int] = field(default_factory=set)
    #: Bumped every game so ``seat 0`` does not always move first.
    round_number: int = 1
    created_at: float = field(default_factory=time.monotonic)
    draws: int = 0

    @property
    def player_count(self) -> int:
        return sum(1 for seat in self.seats if seat.occupied)

    @property
    def is_full(self) -> bool:
        return all(seat.occupied or seat.reserved for seat in self.seats)

    @property
    def is_empty(self) -> bool:
        return not any(seat.occupied for seat in self.seats) and not self.spectators

    def seat_for_mark(self, mark: Mark) -> int:
        """Which seat plays ``mark`` this round.

        Seats swap marks each round so the first-move advantage alternates.
        """
        offset = (self.round_number - 1) % 2
        return (int(mark) - 1 + offset) % 2

    def mark_for_seat(self, seat_index: int) -> Mark:
        """The mark ``seat_index`` is playing this round."""
        offset = (self.round_number - 1) % 2
        return Mark((seat_index - offset) % 2 + 1)

    def sessions(self) -> list[Session]:
        """Every live session in the room, players first."""
        people = [seat.session for seat in self.seats if seat.occupied]
        return [s for s in people if s is not None] + list(self.spectators)

    def broadcast(self, message: dict[str, Any]) -> None:
        for session in self.sessions():
            session.deliver(message)

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------
    def state_payload(self) -> dict[str, Any]:
        """Room membership as sent in ``room_state`` (no tokens, ever)."""
        return {
            "code": self.code,
            "game": self.game_key,
            "title": type(self.game).title,
            "private": self.private,
            "round": self.round_number,
            "draws": self.draws,
            "players": [
                {
                    "seat": index,
                    "name": seat.name or None,
                    "mark": int(self.mark_for_seat(index)),
                    "mark_name": type(self.game).mark_names[
                        int(self.mark_for_seat(index)) - 1
                    ],
                    "online": seat.occupied,
                    "reserved": seat.reserved,
                    "wins": seat.wins,
                }
                for index, seat in enumerate(self.seats)
            ],
            "spectators": [s.name for s in self.spectators],
            "rematch": sorted(self.rematch_votes),
        }

    def game_payload(self) -> dict[str, Any]:
        """Board snapshot as sent in ``game_state``."""
        board = self.game.to_dict()
        payload: dict[str, Any] = {"code": self.code, "board": board}
        if self.game.winner is not None:
            payload["result"] = {
                "outcome": "win",
                "winner_mark": int(self.game.winner),
                "winner_seat": self.seat_for_mark(self.game.winner),
                "win_cells": list(self.game.win_cells),
            }
        elif self.game.is_draw:
            payload["result"] = {"outcome": "draw"}
        return payload

    def reset_game(self) -> None:
        """Start the next round with a fresh board and swapped marks."""
        self.game = create_game(self.game_key)
        self.round_number += 1
        self.rematch_votes.clear()


class Lobby:
    """Owns every session and room on a server instance."""

    def __init__(
        self,
        rng: random.Random | None = None,
        reconnect_grace: float = DEFAULT_RECONNECT_GRACE,
        server_name: str = "board-game-server",
    ) -> None:
        self.rng = rng or random.Random()
        self.reconnect_grace = reconnect_grace
        self.server_name = server_name
        self.sessions: dict[str, Session] = {}
        self.rooms: dict[str, Room] = {}
        #: Sessions waiting for a quick match, keyed by game.
        self.queues: dict[str, list[Session]] = {key: [] for key in GAMES}
        self._counter = 0

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def connect(self, send: Callable[[dict[str, Any]], None]) -> Session:
        """Register a new transport and return its :class:`Session`."""
        self._counter += 1
        session = Session(
            id=f"p{self._counter}",
            send=send,
            token="".join(
                self.rng.choice(string.ascii_letters + string.digits) for _ in range(16)
            ),
        )
        self.sessions[session.id] = session
        return session

    def disconnect(self, session: Session) -> None:
        """Drop a transport, holding any seat open for a possible reconnect."""
        session.connected = False
        self.sessions.pop(session.id, None)
        for queue in self.queues.values():
            if session in queue:
                queue.remove(session)
        room = self._room_of(session)
        if room is None:
            return
        if session in room.spectators:
            room.spectators.remove(session)
        if session.seat is not None:
            seat = room.seats[session.seat]
            if seat.session is session:
                seat.session = None
                seat.vacated_at = time.monotonic()
            room.broadcast(
                proto.notice(
                    f"{session.name} disconnected — seat held for a reconnect."
                )
            )
        self._sync_room(room)
        if room.is_empty and not any(s.reserved for s in room.seats):
            self.rooms.pop(room.code, None)

    def sweep(self, now: float | None = None) -> list[str]:
        """Release seats whose grace period has lapsed; return closed rooms.

        Servers call this periodically. It is a no-op for rooms whose players
        are all still connected.
        """
        now = time.monotonic() if now is None else now
        closed: list[str] = []
        for code, room in list(self.rooms.items()):
            changed = False
            for seat in room.seats:
                if (
                    seat.reserved
                    and seat.vacated_at is not None
                    and now - seat.vacated_at > self.reconnect_grace
                ):
                    seat.token = ""
                    seat.name = ""
                    seat.vacated_at = None
                    changed = True
            if room.is_empty and not any(s.reserved for s in room.seats):
                self.rooms.pop(code, None)
                closed.append(code)
            elif changed:
                room.broadcast(proto.notice("A held seat was released."))
                self._sync_room(room)
        return closed

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def handle(self, session: Session, data: dict[str, Any]) -> None:
        """Process one decoded client frame."""
        kind = data.get("type")
        handler = getattr(self, f"_on_{kind}", None)
        if kind not in proto.CLIENT_MESSAGES or handler is None:
            session.deliver(
                proto.error(proto.ERR_BAD_MESSAGE, f"unsupported message {kind!r}")
            )
            return
        try:
            handler(session, data)
        except proto.ProtocolError as exc:
            session.deliver(proto.error(proto.ERR_BAD_MESSAGE, str(exc)))

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_ping(self, session: Session, data: dict[str, Any]) -> None:
        session.deliver(proto.message(proto.PONG))

    def _on_hello(self, session: Session, data: dict[str, Any]) -> None:
        name = str(data.get("name") or "anonymous").strip()[:24] or "anonymous"
        session.name = name
        resumed = None
        token = data.get("token")
        if isinstance(token, str) and token:
            resumed = self._resume(session, token)
        session.deliver(
            proto.message(
                proto.WELCOME,
                player_id=session.id,
                token=session.token,
                server=self.server_name,
                version=proto.VERSION,
                games=sorted(GAMES),
                resumed=resumed is not None,
            )
        )
        if resumed is not None:
            session.deliver(proto.notice(f"Reconnected to room {resumed.code}."))
            self._sync_room(resumed)
            resumed.broadcast(proto.notice(f"{session.name} reconnected."))

    def _on_create_room(self, session: Session, data: dict[str, Any]) -> None:
        game_key = self._game_key(session, data.get("game", "tictactoe"))
        if game_key is None:
            return
        self._leave_room(session)
        code = _new_code(self.rooms, self.rng)
        room = Room(
            code=code,
            game_key=game_key,
            game=create_game(game_key),
            private=bool(data.get("private", False)),
        )
        self.rooms[code] = room
        self._seat(session, room, 0)
        session.deliver(proto.notice(f"Room {code} created. Share the code to play."))
        self._sync_room(room)

    def _on_join_room(self, session: Session, data: dict[str, Any]) -> None:
        code = str(proto.require(data, "code", str)).strip().upper()
        room = self.rooms.get(code)
        if room is None:
            session.deliver(proto.error(proto.ERR_NO_ROOM, f"no room named {code}"))
            return
        wants_spectate = str(data.get("as", "player")).lower() == "spectator"
        self._leave_room(session)
        if wants_spectate:
            self._add_spectator(session, room)
        else:
            index = self._free_seat(room, session.token)
            if index is None:
                self._add_spectator(session, room)
                session.deliver(
                    proto.notice("Room was full — you joined as spectator.")
                )
            else:
                self._seat(session, room, index)
        self._sync_room(room)

    def _on_quick_match(self, session: Session, data: dict[str, Any]) -> None:
        game_key = self._game_key(session, data.get("game", "tictactoe"))
        if game_key is None:
            return
        self._leave_room(session)
        queue = self.queues[game_key]
        while queue:
            other = queue.pop(0)
            if other.connected and other is not session:
                room = Room(
                    code=_new_code(self.rooms, self.rng),
                    game_key=game_key,
                    game=create_game(game_key),
                )
                self.rooms[room.code] = room
                self._seat(other, room, 0)
                self._seat(session, room, 1)
                room.broadcast(proto.notice("Matched! Good luck."))
                self._sync_room(room)
                return
        if session not in queue:
            queue.append(session)
        session.deliver(proto.message(proto.QUEUED, game=game_key))

    def _on_cancel_match(self, session: Session, data: dict[str, Any]) -> None:
        for queue in self.queues.values():
            if session in queue:
                queue.remove(session)
        session.deliver(proto.notice("Left the matchmaking queue."))

    def _on_list_rooms(self, session: Session, data: dict[str, Any]) -> None:
        rooms = [
            {
                "code": room.code,
                "game": room.game_key,
                "players": room.player_count,
                "spectators": len(room.spectators),
                "in_progress": bool(room.game.history) and not room.game.is_over,
            }
            for room in self.rooms.values()
            if not room.private
        ]
        session.deliver(proto.message(proto.ROOMS, rooms=rooms))

    def _on_move(self, session: Session, data: dict[str, Any]) -> None:
        move = proto.require(data, "move", int)
        room = self._room_of(session)
        if room is None:
            session.deliver(proto.error(proto.ERR_NO_ROOM, "you are not in a room"))
            return
        if session.seat is None:
            session.deliver(
                proto.error(proto.ERR_NOT_PLAYING, "spectators cannot move")
            )
            return
        if room.game.is_over:
            session.deliver(
                proto.error(proto.ERR_GAME_OVER, "this round is already finished")
            )
            return
        if room.player_count < 2:
            session.deliver(
                proto.error(proto.ERR_NOT_PLAYING, "waiting for an opponent")
            )
            return
        if room.mark_for_seat(session.seat) is not room.game.turn:
            session.deliver(proto.error(proto.ERR_NOT_YOUR_TURN, "it is not your turn"))
            return
        try:
            room.game.play(move)
        except IllegalMove as exc:
            session.deliver(proto.error(proto.ERR_ILLEGAL_MOVE, str(exc)))
            return
        if room.game.winner is not None:
            room.seats[room.seat_for_mark(room.game.winner)].wins += 1
        elif room.game.is_draw:
            room.draws += 1
        self._broadcast_game(room)
        if room.game.is_over:
            # Refresh the roster so the win/draw tally updates for everyone.
            self._sync_room(room, include_board=False)

    def _on_rematch(self, session: Session, data: dict[str, Any]) -> None:
        room = self._room_of(session)
        if room is None or session.seat is None:
            session.deliver(
                proto.error(proto.ERR_NOT_PLAYING, "only seated players can rematch")
            )
            return
        if not room.game.is_over:
            session.deliver(
                proto.error(proto.ERR_BAD_MESSAGE, "the current round is still running")
            )
            return
        room.rematch_votes.add(session.seat)
        if len(room.rematch_votes) >= 2:
            room.reset_game()
            room.broadcast(proto.notice("Rematch! Marks have swapped."))
        else:
            room.broadcast(proto.notice(f"{session.name} wants a rematch."))
        self._sync_room(room)

    def _on_chat(self, session: Session, data: dict[str, Any]) -> None:
        text = str(proto.require(data, "text", str)).strip()[:280]
        if not text:
            return
        room = self._room_of(session)
        if room is None:
            session.deliver(proto.error(proto.ERR_NO_ROOM, "you are not in a room"))
            return
        room.broadcast(
            proto.message(proto.CHAT, **{"from": session.name, "text": text})
        )

    def _on_leave(self, session: Session, data: dict[str, Any]) -> None:
        self._leave_room(session, release_seat=True)
        session.deliver(proto.notice("You left the room."))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _game_key(self, session: Session, name: Any) -> str | None:
        try:
            return normalise_game_key(str(name))
        except KeyError:
            session.deliver(
                proto.error(proto.ERR_UNKNOWN_GAME, f"unknown game {name!r}")
            )
            return None

    def _room_of(self, session: Session) -> Room | None:
        if session.room_code is None:
            return None
        return self.rooms.get(session.room_code)

    def _free_seat(self, room: Room, token: str) -> int | None:
        """Index of a seat this token may take, preferring a reserved one."""
        for index, seat in enumerate(room.seats):
            if seat.reserved and seat.token == token:
                return index
        for index, seat in enumerate(room.seats):
            if not seat.occupied and not seat.reserved:
                return index
        return None

    def _seat(self, session: Session, room: Room, index: int) -> None:
        seat = room.seats[index]
        seat.session = session
        seat.name = session.name
        seat.token = session.token
        seat.vacated_at = None
        session.room_code = room.code
        session.seat = index

    def _add_spectator(self, session: Session, room: Room) -> None:
        session.room_code = room.code
        session.seat = None
        if session not in room.spectators:
            room.spectators.append(session)

    def _resume(self, session: Session, token: str) -> Room | None:
        """Rebind ``session`` to a seat reserved for ``token``, if any."""
        for room in self.rooms.values():
            for index, seat in enumerate(room.seats):
                if seat.reserved and seat.token == token:
                    session.token = token
                    self._seat(session, room, index)
                    return room
        return None

    def _leave_room(self, session: Session, release_seat: bool = True) -> None:
        room = self._room_of(session)
        session.room_code = None
        previous_seat = session.seat
        session.seat = None
        if room is None:
            return
        if session in room.spectators:
            room.spectators.remove(session)
        if previous_seat is not None:
            seat = room.seats[previous_seat]
            if seat.session is session:
                seat.session = None
                seat.vacated_at = None if release_seat else time.monotonic()
                if release_seat:
                    seat.token = ""
                    seat.name = ""
                    seat.wins = 0
            room.rematch_votes.discard(previous_seat)
            room.broadcast(proto.notice(f"{session.name} left the room."))
        if room.is_empty and not any(s.reserved for s in room.seats):
            self.rooms.pop(room.code, None)
        else:
            self._sync_room(room)

    def _sync_room(self, room: Room, include_board: bool = True) -> None:
        """Push the room roster (and by default the board) to everyone present."""
        state = proto.message(proto.ROOM_STATE, **room.state_payload())
        for session in room.sessions():
            personal = dict(state)
            personal["you"] = session.id
            personal["seat"] = session.seat
            personal["your_mark"] = (
                int(room.mark_for_seat(session.seat)) if session.is_player else None
            )
            session.deliver(personal)
        if include_board:
            self._broadcast_game(room)

    def _broadcast_game(self, room: Room) -> None:
        """Send the board to every session, each stamped with its own turn flag.

        ``your_turn`` has to be per-recipient, so this cannot go through
        :meth:`Room.broadcast`.
        """
        board = proto.message(proto.GAME_STATE, **room.game_payload())
        for session in room.sessions():
            personal = dict(board)
            personal["your_turn"] = bool(
                session.is_player
                and not room.game.is_over
                and room.player_count == 2
                and room.mark_for_seat(session.seat) is room.game.turn
            )
            session.deliver(personal)
