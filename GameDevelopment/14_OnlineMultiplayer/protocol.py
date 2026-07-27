"""Wire protocol shared by the server and both clients.

Every frame is a single JSON object with a ``"type"`` field. The module keeps
the vocabulary in one place, provides ``encode``/``decode`` helpers with useful
error messages, and offers small builders so callers never hand-write dicts.

Client -> server
----------------
``hello``        ``{name, token?}``  — open a session, optionally resuming one.
``create_room``  ``{game, private?}``
``join_room``    ``{code, as?}``     — ``as`` is ``"player"`` or ``"spectator"``.
``quick_match``  ``{game}``          — join the matchmaking queue.
``cancel_match`` ``{}``
``list_rooms``   ``{}``
``move``         ``{move}``
``rematch``      ``{}``
``chat``         ``{text}``
``leave``        ``{}``
``ping``         ``{}``

Server -> client
----------------
``welcome``      ``{player_id, token, server}``
``room_state``   ``{code, game, players, spectators, you, seat, rematch}``
``game_state``   ``{code, board, your_turn, result?}``
``queued``       ``{game}``
``rooms``        ``{rooms: [...]}``
``chat``         ``{from, text}``
``notice``       ``{text}``          — informational, safe to log or toast.
``error``        ``{code, text}``
``pong``         ``{}``
"""

from __future__ import annotations

import json
from typing import Any

#: Protocol revision, echoed in ``welcome`` so clients can warn on mismatch.
VERSION = 1

# --- client -> server -------------------------------------------------------
HELLO = "hello"
CREATE_ROOM = "create_room"
JOIN_ROOM = "join_room"
QUICK_MATCH = "quick_match"
CANCEL_MATCH = "cancel_match"
LIST_ROOMS = "list_rooms"
MOVE = "move"
REMATCH = "rematch"
CHAT = "chat"
LEAVE = "leave"
PING = "ping"

# --- server -> client -------------------------------------------------------
WELCOME = "welcome"
ROOM_STATE = "room_state"
GAME_STATE = "game_state"
QUEUED = "queued"
ROOMS = "rooms"
NOTICE = "notice"
ERROR = "error"
PONG = "pong"

CLIENT_MESSAGES = frozenset(
    {
        HELLO,
        CREATE_ROOM,
        JOIN_ROOM,
        QUICK_MATCH,
        CANCEL_MATCH,
        LIST_ROOMS,
        MOVE,
        REMATCH,
        CHAT,
        LEAVE,
        PING,
    }
)

SERVER_MESSAGES = frozenset(
    {WELCOME, ROOM_STATE, GAME_STATE, QUEUED, ROOMS, NOTICE, ERROR, PONG}
)

# Error codes used in ``error`` frames.
ERR_BAD_MESSAGE = "bad_message"
ERR_NO_SESSION = "no_session"
ERR_NO_ROOM = "no_room"
ERR_ROOM_FULL = "room_full"
ERR_NOT_PLAYING = "not_playing"
ERR_NOT_YOUR_TURN = "not_your_turn"
ERR_ILLEGAL_MOVE = "illegal_move"
ERR_UNKNOWN_GAME = "unknown_game"
ERR_GAME_OVER = "game_over"


class ProtocolError(ValueError):
    """Raised when a frame cannot be parsed or is missing required fields."""


def encode(message: dict[str, Any]) -> str:
    """Serialise a message dict to a JSON frame."""
    return json.dumps(message, separators=(",", ":"))


def decode(frame: str | bytes) -> dict[str, Any]:
    """Parse a JSON frame into a message dict.

    Raises :class:`ProtocolError` for malformed JSON, non-objects, or frames
    without a string ``type``.
    """
    try:
        data = json.loads(frame)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"frame is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProtocolError("frame must be a JSON object")
    kind = data.get("type")
    if not isinstance(kind, str):
        raise ProtocolError("frame is missing a string 'type'")
    return data


def message(kind: str, **fields: Any) -> dict[str, Any]:
    """Build a message dict of the given ``kind``."""
    return {"type": kind, **fields}


def require(data: dict[str, Any], field: str, expected: type) -> Any:
    """Fetch ``field`` from ``data``, checking its type.

    Booleans are rejected where an ``int`` is expected, since ``bool`` is an
    ``int`` subclass in Python and ``{"move": true}`` should not mean column 1.
    """
    if field not in data:
        raise ProtocolError(f"missing field {field!r}")
    value = data[field]
    if expected is int and isinstance(value, bool):
        raise ProtocolError(f"field {field!r} must be an integer")
    if not isinstance(value, expected):
        raise ProtocolError(f"field {field!r} must be {expected.__name__}")
    return value


def error(code: str, text: str) -> dict[str, Any]:
    """Build an ``error`` frame."""
    return message(ERROR, code=code, text=text)


def notice(text: str) -> dict[str, Any]:
    """Build a ``notice`` frame."""
    return message(NOTICE, text=text)
