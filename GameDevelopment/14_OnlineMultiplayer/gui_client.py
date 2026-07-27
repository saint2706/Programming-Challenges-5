"""Pygame front-end for Tic-Tac-Toe and Connect Four.

One window covers every mode: a menu screen picks the game and how to play
(hotseat, versus the bot, quick match, create/join a room), and the board screen
handles input, animation and the online message pump. Art and audio are the CC0
Kenney assets fetched by :mod:`fetch_assets`; if ``assets/`` is missing the
client falls back to drawn shapes so it still runs.

    python gui_client.py
    python gui_client.py --game c4 --mode ai --difficulty hard
    python gui_client.py --mode online --quick --url ws://host:8765
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import protocol as proto
import pygame
from ai import Bot, Difficulty
from boardgames import GridGame, IllegalMove, Mark, create_game, normalise_game_key
from netclient import DEFAULT_URL, ClientState, NetClient

ASSETS = Path(__file__).resolve().parent / "assets"

WINDOW = (960, 720)
FPS = 60
BOARD_MARGIN = 32
SIDEBAR_WIDTH = 260

# Palette
BG = (22, 25, 37)
PANEL = (31, 36, 52)
PANEL_LIGHT = (44, 51, 71)
BOARD_BLUE = (38, 78, 168)
GRID = (60, 68, 92)
TEXT = (228, 232, 244)
TEXT_DIM = (146, 154, 178)
ACCENT = (255, 205, 76)
P1_COLOUR = (232, 78, 82)
P2_COLOUR = (247, 200, 70)
CHIP_RED = (206, 62, 62)
CHIP_BLUE = (60, 168, 224)
WIN_GLOW = (108, 226, 138)
DANGER = (226, 96, 108)


#: Per-game ink colours, so labels match the sprites on screen.
MARK_COLOURS = {
    "tictactoe": (P1_COLOUR, P2_COLOUR),
    "connect4": (CHIP_RED, CHIP_BLUE),
}


def mark_colour(game_key: str, mark: int) -> tuple[int, int, int]:
    """Colour used for ``mark`` (1 or 2) in ``game_key``."""
    palette = MARK_COLOURS.get(game_key, (P1_COLOUR, P2_COLOUR))
    return palette[max(0, min(1, mark - 1))]


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------
class Assets:
    """Loads the Kenney art/audio, degrading gracefully when files are absent."""

    def __init__(self) -> None:
        self.images: dict[str, pygame.Surface] = {}
        self.sounds: dict[str, pygame.mixer.Sound | None] = {}
        self.missing: list[str] = []
        for name in ("mark_x", "mark_o", "chip_red", "chip_blue"):
            self.images[name] = self._image(f"{name}.png")
        for name in ("sfx_place", "sfx_click", "sfx_win", "sfx_hover"):
            self.sounds[name] = self._sound(f"{name}.ogg")
        self.font_path = ASSETS / "kenney_future.ttf"
        self.mono_path = ASSETS / "kenney_mini_square.ttf"

    def _image(self, filename: str) -> pygame.Surface:
        path = ASSETS / filename
        if not path.exists():
            self.missing.append(filename)
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        return pygame.image.load(str(path)).convert_alpha()

    def _sound(self, filename: str) -> pygame.mixer.Sound | None:
        path = ASSETS / filename
        if not path.exists() or not pygame.mixer.get_init():
            return None
        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error:  # pragma: no cover - depends on audio backend
            return None

    def font(self, size: int, mono: bool = False) -> pygame.font.Font:
        """A Kenney font at ``size``, falling back to Pygame's default."""
        path = self.mono_path if mono else self.font_path
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.Font(None, int(size * 1.25))

    def play(self, name: str, volume: float = 0.6) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.set_volume(volume)
            sound.play()

    @staticmethod
    def tinted(surface: pygame.Surface, colour: tuple[int, int, int]) -> pygame.Surface:
        """A copy of ``surface`` multiplied by ``colour`` (alpha preserved)."""
        clone = surface.copy()
        clone.fill((*colour, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return clone

    @staticmethod
    def scaled(surface: pygame.Surface, size: int) -> pygame.Surface:
        """``surface`` scaled to fit a ``size``-pixel square, keeping aspect."""
        width, height = surface.get_size()
        if width < 2 or height < 2:
            return surface
        factor = size / max(width, height)
        return pygame.transform.smoothscale(
            surface, (max(1, int(width * factor)), max(1, int(height * factor)))
        )


# ---------------------------------------------------------------------------
# Small widgets
# ---------------------------------------------------------------------------
@dataclass
class Button:
    """A rounded rectangle that reports clicks."""

    rect: pygame.Rect
    label: str
    action: str
    enabled: bool = True
    accent: bool = False
    hovered: bool = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.enabled:
            fill, ink = PANEL, TEXT_DIM
        elif self.accent:
            fill, ink = (ACCENT if self.hovered else (214, 170, 58)), (30, 30, 40)
        else:
            fill, ink = (PANEL_LIGHT if self.hovered else PANEL), TEXT
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        pygame.draw.rect(surface, GRID, self.rect, width=2, border_radius=8)
        text = font.render(self.label, True, ink)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def hit(self, position: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(position)


class TextField:
    """A single-line text input used for the room code and server URL."""

    def __init__(self, rect: pygame.Rect, value: str = "", limit: int = 48) -> None:
        self.rect = rect
        self.value = value
        self.limit = limit
        self.focused = False

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                self.focused = False
            elif event.unicode and event.unicode.isprintable():
                if len(self.value) < self.limit:
                    self.value += event.unicode

    def draw(
        self, surface: pygame.Surface, font: pygame.font.Font, placeholder: str = ""
    ) -> None:
        pygame.draw.rect(surface, (16, 18, 28), self.rect, border_radius=6)
        pygame.draw.rect(
            surface,
            ACCENT if self.focused else GRID,
            self.rect,
            width=2,
            border_radius=6,
        )
        shown = self.value or placeholder
        ink = TEXT if self.value else TEXT_DIM
        text = font.render(shown, True, ink)
        surface.blit(
            text, (self.rect.x + 10, self.rect.centery - text.get_height() // 2)
        )
        if self.focused and pygame.time.get_ticks() // 500 % 2 == 0:
            caret_x = self.rect.x + 12 + font.size(self.value)[0]
            pygame.draw.line(
                surface,
                ACCENT,
                (caret_x, self.rect.y + 8),
                (caret_x, self.rect.bottom - 8),
                2,
            )


# ---------------------------------------------------------------------------
# Board rendering
# ---------------------------------------------------------------------------
class BoardView:
    """Maps board cells to screen rectangles and draws the pieces."""

    def __init__(self, game: GridGame, area: pygame.Rect, assets: Assets) -> None:
        self.game = game
        self.assets = assets
        self.connect_style = game.key == "connect4"
        cell = min(
            (area.width - BOARD_MARGIN) // game.cols,
            (area.height - BOARD_MARGIN) // game.rows,
        )
        self.cell = max(24, cell)
        width = self.cell * game.cols
        height = self.cell * game.rows
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = area.center
        self._sprites: dict[tuple[int, int], pygame.Surface] = {}

    def cell_rect(self, index: int) -> pygame.Rect:
        row, col = self.game.coords(index)
        return pygame.Rect(
            self.rect.x + col * self.cell,
            self.rect.y + row * self.cell,
            self.cell,
            self.cell,
        )

    def cell_at(self, position: tuple[int, int]) -> int | None:
        """Board index under ``position``, or ``None`` when outside the board."""
        if not self.rect.collidepoint(position):
            return None
        col = (position[0] - self.rect.x) // self.cell
        row = (position[1] - self.rect.y) // self.cell
        if not self.game.in_bounds(row, col):
            return None
        return self.game.index(row, col)

    def move_at(self, position: tuple[int, int]) -> int | None:
        """Legal move implied by a click at ``position``.

        Connect Four resolves any click in a column to that column's drop.
        """
        if self.connect_style:
            if not self.rect.collidepoint((self.rect.centerx, position[1])):
                if not (self.rect.x <= position[0] < self.rect.right):
                    return None
            col = (position[0] - self.rect.x) // self.cell
            if 0 <= col < self.game.cols and col in self.game.legal_moves():
                return int(col)
            return None
        index = self.cell_at(position)
        if index is None or index not in self.game.legal_moves():
            return None
        return index

    def sprite(self, mark: Mark, size: int) -> pygame.Surface:
        """Cached, tinted, scaled sprite for ``mark``."""
        key = (int(mark), size)
        if key not in self._sprites:
            if self.connect_style:
                name = "chip_red" if mark is Mark.P1 else "chip_blue"
                image = self.assets.images[name]
                surface = self.assets.scaled(image, size)
            else:
                name = "mark_x" if mark is Mark.P1 else "mark_o"
                colour = P1_COLOUR if mark is Mark.P1 else P2_COLOUR
                image = self.assets.tinted(self.assets.images[name], colour)
                surface = self.assets.scaled(image, size)
            if surface.get_width() < 2:  # asset missing: draw a fallback
                surface = self._fallback(mark, size)
            self._sprites[key] = surface
        return self._sprites[key]

    def _fallback(self, mark: Mark, size: int) -> pygame.Surface:
        """Vector stand-in used when the sprite files are not installed."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        colour = mark_colour(self.game.key, int(mark))
        if self.connect_style or mark is Mark.P2:
            pygame.draw.circle(
                surface,
                colour,
                (size // 2, size // 2),
                size // 2 - 4,
                0 if self.connect_style else 6,
            )
        else:
            pad = size // 5
            pygame.draw.line(surface, colour, (pad, pad), (size - pad, size - pad), 8)
            pygame.draw.line(surface, colour, (size - pad, pad), (pad, size - pad), 8)
        return surface

    def draw(
        self,
        surface: pygame.Surface,
        hover_move: int | None = None,
        hover_mark: Mark | None = None,
        win_cells: tuple[int, ...] = (),
        pulse: float = 0.0,
    ) -> None:
        if self.connect_style:
            self._draw_connect4(surface, hover_move, hover_mark, win_cells, pulse)
        else:
            self._draw_tictactoe(surface, hover_move, hover_mark, win_cells, pulse)

    # -- per-game boards ------------------------------------------------
    def _draw_tictactoe(
        self,
        surface: pygame.Surface,
        hover_move: int | None,
        hover_mark: Mark | None,
        win_cells: tuple[int, ...],
        pulse: float,
    ) -> None:
        pygame.draw.rect(surface, PANEL, self.rect.inflate(20, 20), border_radius=14)
        sprite_size = int(self.cell * 0.62)
        for index in range(self.game.rows * self.game.cols):
            rect = self.cell_rect(index)
            inner = rect.inflate(-8, -8)
            highlighted = index in win_cells
            fill = PANEL_LIGHT
            if highlighted:
                glow = 0.55 + 0.45 * math.sin(pulse * 5)
                fill = tuple(
                    int(PANEL_LIGHT[i] + (WIN_GLOW[i] - PANEL_LIGHT[i]) * glow)
                    for i in range(3)
                )
            pygame.draw.rect(surface, fill, inner, border_radius=10)
            pygame.draw.rect(surface, GRID, inner, width=2, border_radius=10)
            mark = self.game.cells[index]
            if mark is not Mark.EMPTY:
                sprite = self.sprite(mark, sprite_size)
                surface.blit(sprite, sprite.get_rect(center=rect.center))
            elif index == hover_move and hover_mark is not None:
                ghost = self.sprite(hover_mark, sprite_size).copy()
                ghost.set_alpha(70)
                surface.blit(ghost, ghost.get_rect(center=rect.center))

    def _draw_connect4(
        self,
        surface: pygame.Surface,
        hover_move: int | None,
        hover_mark: Mark | None,
        win_cells: tuple[int, ...],
        pulse: float,
    ) -> None:
        frame = self.rect.inflate(18, 18)
        pygame.draw.rect(surface, BOARD_BLUE, frame, border_radius=16)
        pygame.draw.rect(surface, (26, 54, 122), frame, width=3, border_radius=16)
        sprite_size = int(self.cell * 0.86)
        radius = int(self.cell * 0.40)
        for index in range(self.game.rows * self.game.cols):
            rect = self.cell_rect(index)
            mark = self.game.cells[index]
            if mark is Mark.EMPTY:
                pygame.draw.circle(surface, BG, rect.center, radius)
                pygame.draw.circle(surface, (18, 40, 96), rect.center, radius, 3)
                continue
            sprite = self.sprite(mark, sprite_size)
            surface.blit(sprite, sprite.get_rect(center=rect.center))
            if index in win_cells:
                # Ring drawn on top of the disc so it stays visible.
                thickness = 3 + int(2 + 2 * math.sin(pulse * 6))
                pygame.draw.circle(
                    surface, WIN_GLOW, rect.center, radius + 4, thickness
                )

        if hover_move is not None and hover_mark is not None:
            landing = self.game.cell_for_move(hover_move)
            ghost = self.sprite(hover_mark, sprite_size).copy()
            ghost.set_alpha(90)
            surface.blit(ghost, ghost.get_rect(center=self.cell_rect(landing).center))
            column_x = self.rect.x + hover_move * self.cell + self.cell // 2
            pygame.draw.polygon(
                surface,
                ACCENT,
                [
                    (column_x - 10, frame.y - 22),
                    (column_x + 10, frame.y - 22),
                    (column_x, frame.y - 6),
                ],
            )


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class App:
    """Owns the window, the current screen and the active match."""

    MODES = (
        ("hotseat", "Two players, one keyboard"),
        ("ai", "Play the computer"),
        ("quick", "Online: quick match"),
        ("create", "Online: create room"),
        ("join", "Online: join by code"),
    )

    def __init__(self, args: argparse.Namespace) -> None:
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:  # pragma: no cover - headless machines have no audio
            pass
        self.screen = pygame.display.set_mode(WINDOW)
        pygame.display.set_caption("Online Multiplayer — Tic-Tac-Toe & Connect Four")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.font = self.assets.font(18)
        self.font_small = self.assets.font(13)
        self.font_big = self.assets.font(34)
        self.font_mono = self.assets.font(13, mono=True)

        self.rng = (
            random.Random(args.seed) if args.seed is not None else random.Random()
        )
        self.player_name = args.name
        self.game_key = args.game or "tictactoe"
        self.difficulty = Difficulty(args.difficulty)
        self.url_field = TextField(pygame.Rect(0, 0, 320, 38), args.url)
        self.code_field = TextField(
            pygame.Rect(0, 0, 150, 38), args.room or "", limit=8
        )

        self.screen_name = "menu"
        self.game: GridGame | None = None
        self.view: BoardView | None = None
        self.bot: Bot | None = None
        self.bot_mark: Mark | None = None
        self.bot_delay = 0.0
        self.local_turn_names = ("Player 1", "Player 2")
        self.net: NetClient | None = None
        self.state = ClientState()
        self.status = "Pick a game and a mode."
        self.pulse = 0.0
        self.running = True
        self.buttons: list[Button] = []
        self.last_hover: int | None = None

        if args.mode:
            self._start_from_args(args)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _start_from_args(self, args: argparse.Namespace) -> None:
        mode = args.mode
        if mode == "online":
            mode = "join" if args.room else ("quick" if args.quick else "create")
        self.start_mode(mode)

    def board_area(self) -> pygame.Rect:
        return pygame.Rect(0, 60, WINDOW[0] - SIDEBAR_WIDTH, WINDOW[1] - 60)

    def start_mode(self, mode: str) -> None:
        """Begin a match in ``mode``, connecting to a server if needed."""
        self.assets.play("sfx_click", 0.4)
        if mode in {"hotseat", "ai"}:
            self._start_offline(mode)
            return
        self._start_online(mode)

    def _start_offline(self, mode: str) -> None:
        self.close_net()
        self.game = create_game(self.game_key)
        self.view = BoardView(self.game, self.board_area(), self.assets)
        self.bot = None
        self.bot_mark = None
        if mode == "ai":
            self.bot_mark = Mark.P2
            self.bot = Bot(self.difficulty, rng=self.rng)
            self.local_turn_names = ("You", f"Computer ({self.difficulty.value})")
        else:
            self.local_turn_names = ("Player 1", "Player 2")
        self.screen_name = "offline"
        self.status = "Your move." if mode == "ai" else "Player 1 to move."

    def _start_online(self, mode: str) -> None:
        self.close_net()
        self.state = ClientState()
        url = self.url_field.value.strip() or DEFAULT_URL
        client = NetClient(url)
        try:
            client.connect()
        except ConnectionError as exc:
            self.status = str(exc)
            self.screen_name = "menu"
            return
        self.net = client
        client.send(proto.message(proto.HELLO, name=self.player_name))
        if mode == "join":
            code = self.code_field.value.strip().upper()
            if not code:
                self.status = "Enter a room code first."
                self.close_net()
                return
            client.send(proto.message(proto.JOIN_ROOM, code=code))
        elif mode == "quick":
            client.send(proto.message(proto.QUICK_MATCH, game=self.game_key))
        else:
            client.send(proto.message(proto.CREATE_ROOM, game=self.game_key))
        self.game = None
        self.view = None
        self.screen_name = "online"
        self.status = f"Connected to {url}."

    def close_net(self) -> None:
        if self.net is not None:
            self.net.send(proto.message(proto.LEAVE))
            self.net.close()
            self.net = None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.pulse += dt
            self.handle_events()
            self.update(dt)
            self.draw()
        self.close_net()
        pygame.quit()
        return 0

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.screen_name == "menu":
                    self.running = False
                else:
                    self.close_net()
                    self.screen_name = "menu"
                    self.status = "Pick a game and a mode."
                return
            if self.screen_name == "menu":
                self.url_field.handle(event)
                self.code_field.handle(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_click(event.pos)
            if event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    button.hovered = button.rect.collidepoint(event.pos)

    def _on_click(self, position: tuple[int, int]) -> None:
        for button in self.buttons:
            if button.hit(position):
                self._on_action(button.action)
                return
        if self.view is None or self.game is None:
            return
        move = self.view.move_at(position)
        if move is None:
            return
        if self.screen_name == "offline":
            if self.bot_mark is not None and self.game.turn is self.bot_mark:
                return
            self._apply_local_move(move)
        elif self.screen_name == "online" and self.state.your_turn:
            self.net and self.net.send(proto.message(proto.MOVE, move=move))

    def _on_action(self, action: str) -> None:
        self.assets.play("sfx_click", 0.4)
        if action == "menu":
            self.close_net()
            self.screen_name = "menu"
            self.status = "Pick a game and a mode."
        elif action == "quit":
            self.running = False
        elif action.startswith("game:"):
            self.game_key = action.split(":", 1)[1]
            if self.screen_name == "menu":
                self.status = f"Game set to {self.game_key}."
        elif action.startswith("difficulty:"):
            self.difficulty = Difficulty(action.split(":", 1)[1])
        elif action.startswith("mode:"):
            self.start_mode(action.split(":", 1)[1])
        elif action == "restart" and self.screen_name == "offline":
            self._start_offline("ai" if self.bot is not None else "hotseat")
        elif action == "undo" and self.screen_name == "offline":
            self._undo_local()
        elif action == "rematch" and self.net is not None:
            self.net.send(proto.message(proto.REMATCH))

    def _apply_local_move(self, move: int) -> None:
        assert self.game is not None
        try:
            self.game.play(move)
        except IllegalMove:
            return
        self.assets.play("sfx_place")
        if self.game.is_over:
            self.assets.play("sfx_win", 0.5)
        self.bot_delay = 0.35

    def _undo_local(self) -> None:
        assert self.game is not None
        steps = 2 if self.bot is not None else 1
        for _ in range(steps):
            if self.game.history:
                self.game.undo()

    def update(self, dt: float) -> None:
        if self.screen_name == "online" and self.net is not None:
            for message in self.net.poll():
                kind = self.state.apply(message)
                if kind == proto.GAME_STATE:
                    self._sync_online_board()
                elif kind == proto.ERROR:
                    self.status = self.state.last_error or "error"
        elif self.screen_name == "offline":
            self._update_bot(dt)

    def _sync_online_board(self) -> None:
        game = self.state.game
        if game is None:
            return
        rebuilt = self.game is None or type(self.game) is not type(game)
        previous = len(self.game.history) if self.game is not None else 0
        self.game = game
        if rebuilt or self.view is None or self.view.game is not game:
            self.view = BoardView(game, self.board_area(), self.assets)
        if len(game.history) > previous:
            self.assets.play("sfx_place")
        if game.is_over and self.state.result:
            self.assets.play("sfx_win", 0.5)

    def _update_bot(self, dt: float) -> None:
        if self.game is None or self.bot is None or self.bot_mark is None:
            return
        if self.game.is_over or self.game.turn is not self.bot_mark:
            return
        # Small pause so the bot's reply is readable rather than instant.
        self.bot_delay -= dt
        if self.bot_delay > 0:
            return
        move = self.bot.choose(self.game)
        self.game.play(move)
        self.assets.play("sfx_place")
        if self.game.is_over:
            self.assets.play("sfx_win", 0.5)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self) -> None:
        self.screen.fill(BG)
        self.buttons = []
        if self.screen_name == "menu":
            self._draw_menu()
        else:
            self._draw_header()
            self._draw_board()
            self._draw_sidebar()
        for button in self.buttons:
            button.draw(self.screen, self.font_small)
        pygame.display.flip()

    def _draw_header(self) -> None:
        pygame.draw.rect(self.screen, PANEL, pygame.Rect(0, 0, WINDOW[0], 56))
        title = self.game.title if self.game else "Board Games"
        self.screen.blit(self.font_big.render(title, True, TEXT), (24, 12))
        if self.assets.missing:
            warn = self.font_small.render(
                "assets missing — run fetch_assets.py", True, DANGER
            )
            self.screen.blit(warn, (WINDOW[0] - warn.get_width() - 24, 20))

    def _draw_board(self) -> None:
        if self.game is None or self.view is None:
            waiting = self.font.render("Waiting for the server…", True, TEXT_DIM)
            self.screen.blit(waiting, waiting.get_rect(center=self.board_area().center))
            return
        hover_move: int | None = None
        hover_mark: Mark | None = None
        if not self.game.is_over and self._local_can_move():
            hover_move = self.view.move_at(pygame.mouse.get_pos())
            hover_mark = self.game.turn
            if hover_move != self.last_hover and hover_move is not None:
                self.assets.play("sfx_hover", 0.25)
            self.last_hover = hover_move
        win_cells = self.game.win_cells if self.game.winner is not None else ()
        self.view.draw(self.screen, hover_move, hover_mark, win_cells, self.pulse)

    def _local_can_move(self) -> bool:
        """Whether the human at this keyboard may click right now."""
        if self.game is None:
            return False
        if self.screen_name == "offline":
            return self.bot_mark is None or self.game.turn is not self.bot_mark
        return self.state.your_turn

    def _draw_sidebar(self) -> None:
        panel = pygame.Rect(
            WINDOW[0] - SIDEBAR_WIDTH, 56, SIDEBAR_WIDTH, WINDOW[1] - 56
        )
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.line(
            self.screen, GRID, (panel.x, panel.y), (panel.x, panel.bottom), 2
        )
        y = panel.y + 16

        y = self._draw_status(panel, y)
        if self.screen_name == "online":
            y = self._draw_roster(panel, y)
            y = self._draw_log(panel, y)
        else:
            y = self._draw_scoreline(panel, y)

        actions = [("menu", "Main menu")]
        if self.screen_name == "offline":
            actions = [("restart", "New game"), ("undo", "Undo"), *actions]
        elif self.game is not None and self.game.is_over:
            actions = [("rematch", "Rematch"), *actions]
        button_y = panel.bottom - 16 - len(actions) * 44
        for action, label in actions:
            rect = pygame.Rect(panel.x + 16, button_y, panel.width - 32, 36)
            self.buttons.append(
                Button(rect, label, action, accent=action in {"rematch", "restart"})
            )
            button_y += 44

    def _draw_status(self, panel: pygame.Rect, y: int) -> int:
        if self.game is not None:
            if self.game.winner is not None:
                name = self.game.mark_names[int(self.game.winner) - 1]
                headline, colour = f"{name} wins!", WIN_GLOW
            elif self.game.is_draw:
                headline, colour = "Draw", ACCENT
            elif self.screen_name == "online" and not self.state.your_turn:
                headline, colour = "Opponent's turn", TEXT_DIM
            else:
                mark = int(self.game.turn)
                headline = f"{self.game.mark_names[mark - 1]} to move"
                colour = mark_colour(self.game.key, mark)
        else:
            headline, colour = "Connecting…", TEXT_DIM
        self.screen.blit(self.font.render(headline, True, colour), (panel.x + 16, y))
        y += 30
        for line in _wrap(self.status, self.font_small, panel.width - 32):
            self.screen.blit(
                self.font_small.render(line, True, TEXT_DIM), (panel.x + 16, y)
            )
            y += 18
        return y + 10

    def _draw_scoreline(self, panel: pygame.Rect, y: int) -> int:
        if self.game is None:
            return y
        for index, name in enumerate(self.local_turn_names):
            glyph = self.game.mark_names[index]
            colour = mark_colour(self.game.key, index + 1)
            text = self.font_small.render(f"{glyph} — {name}", True, colour)
            self.screen.blit(text, (panel.x + 16, y))
            y += 20
        moves = len(self.game.history)
        self.screen.blit(
            self.font_small.render(f"Moves played: {moves}", True, TEXT_DIM),
            (panel.x + 16, y + 6),
        )
        return y + 32

    def _draw_roster(self, panel: pygame.Rect, y: int) -> int:
        room = self.state.room or {}
        code = room.get("code")
        if code:
            label = self.font.render(f"Room {code}", True, ACCENT)
            self.screen.blit(label, (panel.x + 16, y))
            y += 26
        for player in room.get("players", []):
            name = player.get("name") or "(empty)"
            if player["seat"] == self.state.seat:
                name += "  ← you"
            suffix = "" if player.get("online") else "  [offline]"
            game_key = self.game.key if self.game else "tictactoe"
            colour = mark_colour(game_key, int(player.get("mark", 1)))
            text = f"{player.get('mark_name', '?')} {name}{suffix}"
            self.screen.blit(
                self.font_small.render(text[:34], True, colour), (panel.x + 16, y)
            )
            y += 18
            self.screen.blit(
                self.font_small.render(
                    f"   wins: {player.get('wins', 0)}", True, TEXT_DIM
                ),
                (panel.x + 16, y),
            )
            y += 20
        if self.state.queued_for:
            self.screen.blit(
                self.font_small.render("Searching for an opponent…", True, ACCENT),
                (panel.x + 16, y),
            )
            y += 20
        return y + 8

    def _draw_log(self, panel: pygame.Rect, y: int) -> int:
        available = panel.bottom - y - 120
        if available < 40:
            return y
        pygame.draw.line(self.screen, GRID, (panel.x + 16, y), (panel.right - 16, y))
        y += 8
        lines: list[str] = []
        for entry in self.state.log[-12:]:
            lines.extend(_wrap(entry, self.font_mono, panel.width - 32))
        for line in lines[-(available // 16) :]:
            self.screen.blit(
                self.font_mono.render(line, True, TEXT_DIM), (panel.x + 16, y)
            )
            y += 16
        return y

    def _draw_menu(self) -> None:
        title = self.font_big.render("Tic-Tac-Toe & Connect Four", True, TEXT)
        self.screen.blit(title, (60, 48))
        subtitle = self.font_small.render(
            "Local, versus the computer, or online over WebSockets.", True, TEXT_DIM
        )
        self.screen.blit(subtitle, (60, 96))

        y = 150
        self.screen.blit(self.font.render("Game", True, ACCENT), (60, y))
        y += 30
        for key, label in (("tictactoe", "Tic-Tac-Toe"), ("connect4", "Connect Four")):
            rect = pygame.Rect(60, y, 220, 38)
            self.buttons.append(
                Button(rect, label, f"game:{key}", accent=self.game_key == key)
            )
            y += 46

        y += 14
        self.screen.blit(self.font.render("Bot strength", True, ACCENT), (60, y))
        y += 30
        for level in Difficulty:
            rect = pygame.Rect(60, y, 220, 34)
            self.buttons.append(
                Button(
                    rect,
                    level.value.title(),
                    f"difficulty:{level.value}",
                    accent=self.difficulty == level,
                )
            )
            y += 40

        y = 150
        self.screen.blit(self.font.render("Mode", True, ACCENT), (360, y))
        y += 30
        for key, label in self.MODES:
            rect = pygame.Rect(360, y, 300, 40)
            self.buttons.append(Button(rect, label, f"mode:{key}"))
            y += 48

        y += 10
        self.screen.blit(self.font_small.render("Server URL", True, TEXT_DIM), (360, y))
        self.url_field.rect.topleft = (360, y + 18)
        self.url_field.draw(self.screen, self.font_small, DEFAULT_URL)
        self.screen.blit(self.font_small.render("Room code", True, TEXT_DIM), (700, y))
        self.code_field.rect.topleft = (700, y + 18)
        self.code_field.draw(self.screen, self.font_small, "ABCD")

        y += 76
        for line in _wrap(self.status, self.font_small, 560):
            self.screen.blit(self.font_small.render(line, True, ACCENT), (360, y))
            y += 18

        hint = self.font_small.render(
            "ESC quits · start a server with: python server.py", True, TEXT_DIM
        )
        self.screen.blit(hint, (60, WINDOW[1] - 36))
        if self.assets.missing:
            warn = self.font_small.render(
                f"{len(self.assets.missing)} asset(s) missing — run fetch_assets.py",
                True,
                DANGER,
            )
            self.screen.blit(warn, (60, WINDOW[1] - 58))


def _wrap(text: str, font: pygame.font.Font, width: int) -> list[str]:
    """Greedy word wrap of ``text`` to ``width`` pixels."""
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pygame board game client")
    parser.add_argument("--game", default=None, help="tictactoe/ttt or connect4/c4")
    parser.add_argument(
        "--mode",
        choices=["hotseat", "ai", "online"],
        default=None,
        help="skip the menu and start in this mode",
    )
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty],
        default=Difficulty.MEDIUM.value,
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="server WebSocket URL")
    parser.add_argument("--room", default=None, help="room code to join")
    parser.add_argument("--quick", action="store_true", help="use quick match")
    parser.add_argument(
        "--name",
        default=os.environ.get("USER") or os.environ.get("USERNAME") or "player",
    )
    parser.add_argument("--seed", type=int, default=None, help="seed the bot's RNG")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.game:
        try:
            args.game = normalise_game_key(args.game)
        except KeyError:
            print(f"Unknown game {args.game!r}. Try ttt or c4.", file=sys.stderr)
            return 2
    return App(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
