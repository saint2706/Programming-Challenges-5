"""WebSocket front door for the :class:`~lobby.Lobby`.

This module is a thin adapter: it decodes frames, hands them to the lobby, and
pumps the lobby's replies back out. All the interesting rules live in
:mod:`lobby` and :mod:`boardgames`.

Run it with::

    python server.py --host 0.0.0.0 --port 8765
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
from typing import Any

import protocol as proto
import websockets
from lobby import DEFAULT_RECONNECT_GRACE, Lobby

LOGGER = logging.getLogger("boardgame.server")

#: How often expired reconnect reservations are swept, in seconds.
SWEEP_INTERVAL = 15.0


class GameServer:
    """Bridges ``websockets`` connections onto a :class:`Lobby`."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        reconnect_grace: float = DEFAULT_RECONNECT_GRACE,
    ) -> None:
        self.host = host
        self.port = port
        self.lobby = Lobby(reconnect_grace=reconnect_grace)

    async def handler(self, websocket: Any) -> None:
        """Serve one client connection for its whole lifetime."""
        outbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        session = self.lobby.connect(outbox.put_nowait)
        peer = getattr(websocket, "remote_address", None)
        LOGGER.info("connected: %s from %s", session.id, peer)
        writer = asyncio.create_task(self._drain(websocket, outbox))
        try:
            async for raw in websocket:
                try:
                    data = proto.decode(raw)
                except proto.ProtocolError as exc:
                    session.deliver(proto.error(proto.ERR_BAD_MESSAGE, str(exc)))
                    continue
                self.lobby.handle(session, data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.lobby.disconnect(session)
            writer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await writer
            LOGGER.info("disconnected: %s", session.id)

    @staticmethod
    async def _drain(websocket: Any, outbox: asyncio.Queue) -> None:
        """Forward queued lobby messages to the socket until cancelled."""
        while True:
            message = await outbox.get()
            try:
                await websocket.send(proto.encode(message))
            except websockets.exceptions.ConnectionClosed:
                return

    async def _sweeper(self) -> None:
        """Periodically release seats whose reconnect window has closed."""
        while True:
            await asyncio.sleep(SWEEP_INTERVAL)
            for code in self.lobby.sweep():
                LOGGER.info("closed empty room %s", code)

    async def serve_forever(self) -> None:
        """Listen until the process is interrupted."""
        sweeper = asyncio.create_task(self._sweeper())
        try:
            async with websockets.serve(self.handler, self.host, self.port):
                LOGGER.info("listening on ws://%s:%s", self.host, self.port)
                await asyncio.Future()
        finally:
            sweeper.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sweeper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Online board game server")
    parser.add_argument("--host", default="127.0.0.1", help="interface to bind")
    parser.add_argument("--port", type=int, default=8765, help="port to bind")
    parser.add_argument(
        "--reconnect-grace",
        type=float,
        default=DEFAULT_RECONNECT_GRACE,
        help="seconds a dropped player's seat is held open",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="log every connection event"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )
    server = GameServer(args.host, args.port, args.reconnect_grace)
    try:
        asyncio.run(server.serve_forever())
    except KeyboardInterrupt:
        LOGGER.info("shutting down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
