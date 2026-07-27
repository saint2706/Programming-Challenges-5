"""Pygame front-end for the tower defense engine in :mod:`core`.

The renderer owns no rules: it draws whatever :class:`core.TowerDefenseGame`
currently holds, forwards clicks to ``build``/``upgrade``/``sell``, and turns the
engine's event queue into sounds and explosion puffs. Art and audio are the CC0
Kenney assets fetched by :mod:`fetch_assets`; when ``assets/`` is missing the
game still runs with drawn shapes.

    python main.py
    python main.py --level 2
    python main.py --list-levels

Press F1 in game for the control list.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame
from core import (
    ENEMY_KINDS,
    TICK,
    TOWER_KINDS,
    BuildError,
    Enemy,
    GameEvent,
    GameStatus,
    Level,
    TargetMode,
    Tower,
    TowerDefenseGame,
    Vec2,
    discover_levels,
    tile_label,
)

ASSETS = Path(__file__).resolve().parent / "assets"

HEADER_HEIGHT = 44
SIDEBAR_WIDTH = 268
MIN_BOARD_HEIGHT = 660
FPS = 60
#: Speed multipliers cycled by the speed button / F key.
SPEEDS = (1.0, 2.0, 4.0)

# Palette
BG = (24, 27, 38)
PANEL = (32, 37, 53)
PANEL_LIGHT = (46, 53, 74)
GRID_LINE = (58, 66, 90)
TEXT = (230, 234, 246)
TEXT_DIM = (146, 155, 180)
ACCENT = (255, 205, 76)
GOLD = (255, 205, 76)
GOOD = (110, 224, 140)
DANGER = (228, 92, 96)
RANGE_OK = (110, 224, 140)
RANGE_BAD = (228, 92, 96)
PATH_TINT = (168, 124, 74)
GRASS_TINT = (74, 148, 96)

#: Multiplied over a turret sprite so kinds read apart at a glance. The Kenney
#: pack ships grey turrets only, so frost gets an icy wash.
TOWER_TINTS = {"frost": (150, 212, 255), "flak": (232, 226, 210)}

CONTROLS = [
    ("Left click plot", "build the selected tower"),
    ("Left click tower", "select it (shows range)"),
    ("1 - 5", "pick a tower from the shop"),
    ("U / S", "upgrade / sell the selected tower"),
    ("T", "cycle the selected tower's target mode"),
    ("SPACE", "send the next wave now"),
    ("P", "pause"),
    ("F", "cycle game speed"),
    ("R", "restart the level"),
    ("N / B", "next / previous level"),
    ("F1", "toggle this help"),
    ("ESC", "deselect, or quit"),
]


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
class Assets:
    """Sprite/sound loader that tolerates a missing ``assets/`` directory."""

    IMAGES = (
        "tile_grass",
        "tile_dirt",
        "plot_open",
        "base_stone",
        "turret_cannon",
        "turret_frost",
        "turret_mortar",
        "turret_gatling",
        "turret_flak",
        "enemy_grunt",
        "enemy_runner",
        "enemy_armoured",
        "enemy_boss",
        "enemy_flyer",
        "bullet",
        "shell",
        "frost_bolt",
        "rocket",
        "explosion",
        "tree",
        "bush",
        "rock",
    )
    SOUNDS = (
        "sfx_shoot",
        "sfx_explosion",
        "sfx_build",
        "sfx_upgrade",
        "sfx_leak",
        "sfx_wave",
    )

    #: Sprites whose transparent padding is cropped before scaling. The Kenney
    #: tiles are 64px cells with the artwork floating in the middle, so units and
    #: projectiles would otherwise render at half the size they are given.
    TRIM = frozenset(
        {
            "turret_cannon",
            "turret_frost",
            "turret_mortar",
            "turret_gatling",
            "turret_flak",
            "enemy_grunt",
            "enemy_runner",
            "enemy_armoured",
            "enemy_boss",
            "enemy_flyer",
            "bullet",
            "shell",
            "frost_bolt",
            "rocket",
            "explosion",
            "tree",
            "bush",
            "rock",
        }
    )

    def __init__(self) -> None:
        self.images: dict[str, pygame.Surface | None] = {}
        self.sounds: dict[str, pygame.mixer.Sound | None] = {}
        self.missing: list[str] = []
        for name in self.IMAGES:
            self.images[name] = self._image(f"{name}.png")
        for name in self.SOUNDS:
            self.sounds[name] = self._sound(f"{name}.ogg")
        self.font_path = ASSETS / "kenney_future.ttf"
        self.mono_path = ASSETS / "kenney_mini_square.ttf"
        self._scaled: dict[tuple, pygame.Surface] = {}

    def _image(self, filename: str) -> pygame.Surface | None:
        path = ASSETS / filename
        if not path.exists():
            self.missing.append(filename)
            return None
        image = pygame.image.load(str(path)).convert_alpha()
        if path.stem in self.TRIM:
            image = self._trim(image)
        return image

    @staticmethod
    def _trim(image: pygame.Surface) -> pygame.Surface:
        """Crop fully transparent margins, then pad back to a square.

        Keeping the result square means rotating it around its centre does not
        shift the sprite off its tile.
        """
        bounds = image.get_bounding_rect()
        if bounds.width < 2 or bounds.height < 2:
            return image
        side = max(bounds.width, bounds.height)
        square = pygame.Surface((side, side), pygame.SRCALPHA)
        square.blit(
            image,
            ((side - bounds.width) // 2, (side - bounds.height) // 2),
            bounds,
        )
        return square

    def _sound(self, filename: str) -> pygame.mixer.Sound | None:
        path = ASSETS / filename
        if not path.exists() or not pygame.mixer.get_init():
            return None
        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error:  # pragma: no cover - audio backend dependent
            return None

    def font(self, size: int, mono: bool = False) -> pygame.font.Font:
        path = self.mono_path if mono else self.font_path
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.Font(None, int(size * 1.3))

    def scaled(
        self, name: str, size: int, tint: tuple[int, int, int] | None = None
    ) -> pygame.Surface | None:
        """``name`` scaled to a ``size``-pixel square, optionally tinted. Cached."""
        key = (name, size, tint)
        if key not in self._scaled:
            image = self.images.get(name)
            if image is None:
                return None
            scaled = pygame.transform.smoothscale(image, (size, size))
            if tint is not None:
                scaled = scaled.copy()
                scaled.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._scaled[key] = scaled
        return self._scaled[key]

    def play(self, name: str, volume: float = 0.5) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.set_volume(volume)
            sound.play()


# ---------------------------------------------------------------------------
# Widgets and effects
# ---------------------------------------------------------------------------
@dataclass
class Button:
    """A clickable rounded rectangle in the sidebar."""

    rect: pygame.Rect
    label: str
    action: str
    enabled: bool = True
    accent: bool = False
    hovered: bool = False
    #: When ``False`` the button is a pure hit area — something else drew it.
    visible: bool = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        if not self.enabled:
            fill, ink = PANEL, (96, 103, 126)
        elif self.accent:
            fill, ink = (ACCENT if self.hovered else (214, 170, 58)), (28, 28, 38)
        else:
            fill, ink = (PANEL_LIGHT if self.hovered else PANEL), TEXT
        pygame.draw.rect(surface, fill, self.rect, border_radius=7)
        pygame.draw.rect(surface, GRID_LINE, self.rect, width=2, border_radius=7)
        text = font.render(self.label, True, ink)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def hit(self, position: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(position)


@dataclass
class Puff:
    """A short-lived explosion sprite spawned from a ``hit``/``kill`` event."""

    position: Vec2
    life: float
    max_life: float
    size: int

    def update(self, dt: float) -> bool:
        self.life -= dt
        return self.life > 0

    @property
    def fraction(self) -> float:
        return max(0.0, self.life / self.max_life)


@dataclass
class FloatingText:
    """Gold/damage feedback that drifts upward and fades."""

    position: Vec2
    text: str
    colour: tuple[int, int, int]
    life: float = 0.9

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.position = Vec2(self.position.x, self.position.y - 26 * dt)
        return self.life > 0


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class TowerDefenseApp:
    """Window, input handling and rendering for one run at a time."""

    def __init__(
        self, level_paths: list[Path], index: int = 0, seed: int | None = None
    ) -> None:
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:  # pragma: no cover - headless machines have no audio
            pass
        self.level_paths = level_paths
        self.level_index = index % len(level_paths)
        self.seed = seed
        # The window has to exist before any sprite is converted, so size it
        # from the starting level up front; load_level resizes if needed.
        first = Level.load(self.level_paths[self.level_index])
        self.screen: pygame.Surface | None = pygame.display.set_mode(
            (
                first.width + SIDEBAR_WIDTH,
                max(MIN_BOARD_HEIGHT, first.height) + HEADER_HEIGHT,
            )
        )
        self.assets = Assets()
        self.font = self.assets.font(16)
        self.font_small = self.assets.font(12)
        self.font_big = self.assets.font(26)
        self.font_mono = self.assets.font(12, mono=True)
        self.clock = pygame.time.Clock()
        self.buttons: list[Button] = []
        self.puffs: list[Puff] = []
        self.floaters: list[FloatingText] = []
        self.shop_selection: str | None = "gun"
        self.selected_tile: tuple[int, int] | None = None
        self.speed_index = 0
        self.paused = False
        self.show_help = False
        self.message = ""
        self.message_timer = 0.0
        self.running = True
        self._carry = 0.0
        self.load_level(self.level_index)

    # ------------------------------------------------------------------
    # Level lifecycle
    # ------------------------------------------------------------------
    def load_level(self, index: int) -> None:
        self.level_index = index % len(self.level_paths)
        self.level = Level.load(self.level_paths[self.level_index])
        self.game = TowerDefenseGame(self.level, seed=self.seed)
        self.path_tiles = set(self.level.path_tiles())
        self.decor = {(d[0], d[1]): d[2] for d in self.level.decor}
        self.tile = self.level.tile_size
        self.board_height = max(MIN_BOARD_HEIGHT, self.level.height)
        size = (self.level.width + SIDEBAR_WIDTH, self.board_height + HEADER_HEIGHT)
        if self.screen is None or self.screen.get_size() != size:
            self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption(f"Tower Defense — {self.level.name}")
        # Short maps sit centred in the taller window rather than clinging to the top.
        self.board_origin = (
            0,
            HEADER_HEIGHT + (self.board_height - self.level.height) // 2,
        )
        self.selected_tile = None
        self.puffs.clear()
        self.floaters.clear()
        self._carry = 0.0
        self.paused = False
        self.terrain = self._render_terrain()
        self.notify(f"{self.level.name} — {self.level.description}")

    def _render_terrain(self) -> pygame.Surface:
        """Pre-render the static map so each frame only draws entities."""
        surface = pygame.Surface((self.level.width, self.level.height))
        surface.fill(BG)
        grass = self.assets.scaled("tile_grass", self.tile)
        dirt = self.assets.scaled("tile_dirt", self.tile)
        plot = self.assets.scaled("plot_open", self.tile)
        for row in range(self.level.rows):
            for col in range(self.level.cols):
                rect = pygame.Rect(
                    col * self.tile, row * self.tile, self.tile, self.tile
                )
                on_path = (col, row) in self.path_tiles
                sprite = dirt if on_path else grass
                if sprite is not None:
                    surface.blit(sprite, rect)
                else:
                    surface.fill(PATH_TINT if on_path else GRASS_TINT, rect)
        for col, row in self.level.plots:
            rect = pygame.Rect(col * self.tile, row * self.tile, self.tile, self.tile)
            if plot is not None:
                surface.blit(plot, rect)
            else:
                pygame.draw.rect(surface, PANEL_LIGHT, rect.inflate(-6, -6), 3)
        for (col, row), kind in self.decor.items():
            sprite = self.assets.scaled(kind, self.tile)
            if sprite is not None:
                surface.blit(sprite, (col * self.tile, row * self.tile))
        self._draw_endpoints(surface)
        return surface

    def _draw_endpoints(self, surface: pygame.Surface) -> None:
        """Mark the entry and exit tiles so the path reads at a glance."""
        for tile, colour, label in (
            (self.level.waypoints[0], GOOD, "IN"),
            (self.level.waypoints[-1], DANGER, "OUT"),
        ):
            rect = pygame.Rect(
                tile[0] * self.tile, tile[1] * self.tile, self.tile, self.tile
            )
            pygame.draw.rect(surface, colour, rect, width=3)
            text = self.font_small.render(label, True, colour)
            # Entry/exit tiles sit on the map edge, where a centred label would
            # spill off the surface, so clamp it back inside.
            surface.blit(
                text, text.get_rect(center=rect.center).clamp(surface.get_rect())
            )

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def to_screen(self, position: Vec2) -> tuple[int, int]:
        return (
            int(position.x + self.board_origin[0]),
            int(position.y + self.board_origin[1]),
        )

    def tile_under(self, pixel: tuple[int, int]) -> tuple[int, int] | None:
        x = pixel[0] - self.board_origin[0]
        y = pixel[1] - self.board_origin[1]
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return None
        tile = (int(x // self.tile), int(y // self.tile))
        return tile if self.level.in_bounds(*tile) else None

    def notify(self, text: str, seconds: float = 4.0) -> None:
        self.message = text
        self.message_timer = seconds

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        return 0

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._on_click(event.pos)
                elif event.button == 3:
                    self.shop_selection = None
                    self.selected_tile = None
            elif event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    button.hovered = button.rect.collidepoint(event.pos)

    def _on_key(self, key: int) -> None:
        shop_keys = {
            pygame.K_1: "gun",
            pygame.K_2: "gatling",
            pygame.K_3: "frost",
            pygame.K_4: "mortar",
            pygame.K_5: "flak",
        }
        if key in shop_keys:
            self.shop_selection = shop_keys[key]
            self.selected_tile = None
        elif key == pygame.K_ESCAPE:
            if self.shop_selection or self.selected_tile or self.show_help:
                self.shop_selection = None
                self.selected_tile = None
                self.show_help = False
            else:
                self.running = False
        elif key == pygame.K_SPACE:
            self._action("next_wave")
        elif key == pygame.K_p:
            self._action("pause")
        elif key == pygame.K_f:
            self._action("speed")
        elif key == pygame.K_r:
            self._action("restart")
        elif key == pygame.K_n:
            self._action("next_level")
        elif key == pygame.K_b:
            self.load_level(self.level_index - 1)
        elif key == pygame.K_u:
            self._action("upgrade")
        elif key == pygame.K_s:
            self._action("sell")
        elif key == pygame.K_t:
            self._action("target")
        elif key == pygame.K_F1:
            self.show_help = not self.show_help

    def _on_click(self, position: tuple[int, int]) -> None:
        for button in self.buttons:
            if button.hit(position):
                self._action(button.action)
                return
        tile = self.tile_under(position)
        if tile is None:
            return
        if self.game.tower_at(tile) is not None:
            self.selected_tile = tile
            self.shop_selection = None
            return
        if self.shop_selection is None:
            self.selected_tile = None
            return
        try:
            tower = self.game.build(tile, self.shop_selection)
        except BuildError as exc:
            self.notify(str(exc), 2.5)
            return
        self.selected_tile = tile
        self.floaters.append(FloatingText(tower.position, f"-{tower.kind.cost}", GOLD))

    def _action(self, action: str) -> None:
        try:
            if action == "next_wave":
                wave = self.game.start_wave()
                self.notify(f"Wave {self.game.wave_number}: {wave.summary()}")
            elif action == "pause":
                self.paused = not self.paused
                self.notify("Paused" if self.paused else "Resumed", 1.5)
            elif action == "speed":
                self.speed_index = (self.speed_index + 1) % len(SPEEDS)
                self.notify(f"Speed {SPEEDS[self.speed_index]:g}x", 1.5)
            elif action == "restart":
                self.load_level(self.level_index)
            elif action == "next_level":
                self.load_level(self.level_index + 1)
            elif action == "upgrade" and self.selected_tile:
                tower = self.game.upgrade(self.selected_tile)
                self.assets.play("sfx_upgrade", 0.5)
                self.notify(f"{tile_label(self.selected_tile)} → {tower.label}", 2.0)
            elif action == "sell" and self.selected_tile:
                refund = self.game.sell(self.selected_tile)
                centre = self.level.tile_centre(*self.selected_tile)
                self.floaters.append(FloatingText(centre, f"+{refund}", GOLD))
                self.selected_tile = None
            elif action == "target" and self.selected_tile:
                tower = self.game.tower_at(self.selected_tile)
                if tower is not None:
                    modes = list(TargetMode)
                    nxt = modes[(modes.index(tower.target_mode) + 1) % len(modes)]
                    self.game.set_target_mode(self.selected_tile, nxt)
                    self.notify(f"Targeting: {nxt.value}", 1.5)
            elif action.startswith("shop:"):
                self.shop_selection = action.split(":", 1)[1]
                self.selected_tile = None
        except BuildError as exc:
            self.notify(str(exc), 2.5)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.message_timer = max(0.0, self.message_timer - dt)
        self.puffs = [p for p in self.puffs if p.update(dt)]
        self.floaters = [f for f in self.floaters if f.update(dt)]
        if self.paused or self.game.is_over:
            self.game.drain_events()
            return
        # Feed the engine whole fixed ticks so it stays deterministic even
        # though the display runs at whatever rate the machine manages.
        self._carry += dt * SPEEDS[self.speed_index]
        ticks = int(self._carry / TICK)
        self._carry -= ticks * TICK
        self.game.run_ticks(min(ticks, 40))
        self._consume_events(self.game.drain_events())
        if self.selected_tile and self.game.tower_at(self.selected_tile) is None:
            self.selected_tile = None

    def _consume_events(self, events: list[GameEvent]) -> None:
        """Turn engine events into sounds, puffs and floating text."""
        shots = 0
        for event in events:
            if event.kind == "shoot":
                shots += 1
            elif event.kind == "hit":
                self.puffs.append(
                    Puff(event.position, 0.22, 0.22, int(self.tile * 0.5))
                )
            elif event.kind == "kill":
                self.puffs.append(Puff(event.position, 0.4, 0.4, int(self.tile * 0.8)))
                bounty = ENEMY_KINDS[_enemy_key(event.detail)].bounty
                self.floaters.append(FloatingText(event.position, f"+{bounty}", GOLD))
                self.assets.play("sfx_explosion", 0.22)
            elif event.kind == "leak":
                self.floaters.append(FloatingText(event.position, "LEAK!", DANGER))
                self.assets.play("sfx_leak", 0.55)
                self.notify(f"{event.detail} got through!", 2.0)
            elif event.kind in {"wave", "end"}:
                self.assets.play("sfx_wave", 0.45)
                self.notify(event.detail, 3.5)
            elif event.kind == "build":
                self.assets.play("sfx_build", 0.45)
        if shots:
            # One sound per frame however many towers fired, or it turns to mush.
            self.assets.play("sfx_shoot", 0.14)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self) -> None:
        assert self.screen is not None
        self.screen.fill(BG)
        self.buttons = []
        self.screen.blit(self.terrain, self.board_origin)
        self._draw_hover()
        self._draw_towers()
        self._draw_enemies()
        self._draw_projectiles()
        self._draw_effects()
        self._draw_header()
        self._draw_sidebar()
        if self.game.is_over:
            self._draw_verdict()
        if self.show_help:
            self._draw_help()
        for button in self.buttons:
            button.draw(self.screen, self.font_small)
        pygame.display.flip()

    def _draw_hover(self) -> None:
        assert self.screen is not None
        tile = self.tile_under(pygame.mouse.get_pos())
        if tile is None:
            return
        rect = pygame.Rect(
            tile[0] * self.tile + self.board_origin[0],
            tile[1] * self.tile + self.board_origin[1],
            self.tile,
            self.tile,
        )
        kind = TOWER_KINDS.get(self.shop_selection or "")
        if kind is not None:
            ok = self.game.is_buildable(tile) and self.game.gold >= kind.cost
            colour = RANGE_OK if ok else RANGE_BAD
            pygame.draw.rect(self.screen, colour, rect, width=3, border_radius=4)
            if self.game.is_buildable(tile):
                self._draw_range(rect.center, kind.tier(0).range, colour)
        elif self.game.tower_at(tile) is not None:
            pygame.draw.rect(self.screen, ACCENT, rect, width=2, border_radius=4)

    def _draw_range(self, centre: tuple[int, int], radius: float, colour) -> None:
        assert self.screen is not None
        overlay = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            overlay, (*colour, 34), (int(radius) + 2, int(radius) + 2), int(radius)
        )
        pygame.draw.circle(
            overlay, (*colour, 150), (int(radius) + 2, int(radius) + 2), int(radius), 2
        )
        self.screen.blit(overlay, overlay.get_rect(center=centre))

    def _draw_towers(self) -> None:
        assert self.screen is not None
        base = self.assets.scaled("base_stone", self.tile)
        for tile, tower in self.game.towers.items():
            centre = self.to_screen(tower.position)
            rect = pygame.Rect(0, 0, self.tile, self.tile)
            rect.center = centre
            if base is not None:
                self.screen.blit(base, rect)
            else:
                pygame.draw.rect(
                    self.screen, PANEL_LIGHT, rect.inflate(-4, -4), border_radius=6
                )
            head = self.assets.scaled(
                tower.kind.sprite,
                int(self.tile * 0.8),
                TOWER_TINTS.get(tower.kind.key),
            )
            if head is not None:
                rotated = pygame.transform.rotate(head, -tower.angle)
                self.screen.blit(rotated, rotated.get_rect(center=centre))
            else:
                self._draw_fallback_turret(centre, tower)
            for pip in range(tower.tier):
                pygame.draw.circle(
                    self.screen, ACCENT, (rect.x + 7 + pip * 8, rect.bottom - 6), 3
                )
            if tile == self.selected_tile:
                pygame.draw.rect(self.screen, ACCENT, rect, width=2, border_radius=6)
                self._draw_range(centre, tower.range, ACCENT)

    def _draw_fallback_turret(self, centre: tuple[int, int], tower: Tower) -> None:
        """Vector turret used when the sprite sheet is not installed."""
        assert self.screen is not None
        pygame.draw.circle(self.screen, (170, 176, 190), centre, int(self.tile * 0.3))
        angle = math.radians(tower.angle - 90)
        tip = (
            centre[0] + math.cos(angle) * self.tile * 0.45,
            centre[1] + math.sin(angle) * self.tile * 0.45,
        )
        pygame.draw.line(self.screen, (110, 116, 130), centre, tip, 6)

    def _draw_enemies(self) -> None:
        assert self.screen is not None
        for enemy in self.game.enemies:
            if not enemy.alive:
                continue
            centre = self.to_screen(enemy.position)
            size = int(self.tile * (0.9 if enemy.kind.key == "juggernaut" else 0.7))
            sprite = self.assets.scaled(enemy.kind.sprite, size)
            if sprite is not None:
                if enemy.slow_timer > 0:
                    sprite = sprite.copy()
                    sprite.fill(
                        (150, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT
                    )
                angle = enemy.heading.angle_degrees()
                rotated = pygame.transform.rotate(sprite, -angle)
                self.screen.blit(rotated, rotated.get_rect(center=centre))
            else:
                colour = (150, 200, 255) if enemy.slow_timer > 0 else DANGER
                pygame.draw.circle(self.screen, colour, centre, size // 3)
            if enemy.kind.flying:
                # A faint shadow sells the difference between air and ground.
                pygame.draw.circle(
                    self.screen,
                    (16, 18, 26),
                    (centre[0] + 5, centre[1] + 8),
                    size // 5,
                    1,
                )
            self._draw_health_bar(centre, size, enemy)

    def _draw_health_bar(
        self, centre: tuple[int, int], size: int, enemy: Enemy
    ) -> None:
        assert self.screen is not None
        width = max(18, size)
        rect = pygame.Rect(0, 0, width, 4)
        rect.center = (centre[0], centre[1] - size // 2 - 6)
        pygame.draw.rect(self.screen, (18, 20, 30), rect)
        fraction = enemy.hp_fraction
        fill = pygame.Rect(rect.x, rect.y, int(rect.width * fraction), rect.height)
        colour = GOOD if fraction > 0.6 else (ACCENT if fraction > 0.3 else DANGER)
        pygame.draw.rect(self.screen, colour, fill)

    def _draw_projectiles(self) -> None:
        assert self.screen is not None
        for projectile in self.game.projectiles:
            centre = self.to_screen(projectile.position)
            sprite = self.assets.scaled(projectile.sprite, int(self.tile * 0.34))
            if sprite is not None:
                rotated = pygame.transform.rotate(sprite, -projectile.angle)
                self.screen.blit(rotated, rotated.get_rect(center=centre))
            else:
                pygame.draw.circle(self.screen, ACCENT, centre, 4)

    def _draw_effects(self) -> None:
        assert self.screen is not None
        for puff in self.puffs:
            size = max(4, int(puff.size * (1.4 - puff.fraction)))
            sprite = self.assets.scaled("explosion", size)
            centre = self.to_screen(puff.position)
            if sprite is not None:
                faded = sprite.copy()
                faded.set_alpha(int(255 * puff.fraction))
                self.screen.blit(faded, faded.get_rect(center=centre))
            else:
                pygame.draw.circle(self.screen, ACCENT, centre, size // 2, 2)
        for floater in self.floaters:
            text = self.font_small.render(floater.text, True, floater.colour)
            text.set_alpha(int(255 * min(1.0, floater.life / 0.9)))
            self.screen.blit(
                text, text.get_rect(center=self.to_screen(floater.position))
            )

    def _draw_header(self) -> None:
        assert self.screen is not None
        width = self.screen.get_width()
        pygame.draw.rect(self.screen, PANEL, pygame.Rect(0, 0, width, HEADER_HEIGHT))
        self.screen.blit(self.font_big.render(self.level.name, True, TEXT), (16, 9))
        stats = [
            (f"{self.game.gold}g", GOLD),
            (f"{self.game.lives} lives", GOOD if self.game.lives > 5 else DANGER),
            (f"wave {self.game.wave_number}/{self.game.total_waves}", TEXT),
            (f"score {self.game.score}", TEXT_DIM),
            (
                f"{SPEEDS[self.speed_index]:g}x",
                ACCENT if self.speed_index else TEXT_DIM,
            ),
        ]
        x = width - 16
        for text, colour in reversed(stats):
            rendered = self.font.render(text, True, colour)
            x -= rendered.get_width() + 18
            self.screen.blit(rendered, (x, 14))

    def _draw_sidebar(self) -> None:
        assert self.screen is not None
        panel = pygame.Rect(
            self.screen.get_width() - SIDEBAR_WIDTH,
            HEADER_HEIGHT,
            SIDEBAR_WIDTH,
            self.screen.get_height() - HEADER_HEIGHT,
        )
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.line(
            self.screen, GRID_LINE, (panel.x, panel.y), (panel.x, panel.bottom), 2
        )
        y = panel.y + 10
        y = self._draw_phase(panel, y)
        y = self._draw_shop(panel, y)
        y = self._draw_selection(panel, y)
        self._draw_footer(panel)

    def _draw_phase(self, panel: pygame.Rect, y: int) -> int:
        assert self.screen is not None
        game = self.game
        if game.status is GameStatus.BUILDING:
            headline, colour = "Build phase", GOOD
            detail = f"next wave in {max(0.0, game.break_timer):.1f}s"
        elif game.status is GameStatus.WAVE:
            headline, colour = f"Wave {game.wave_number}", ACCENT
            detail = f"{game.alive_enemies} on field · {game.pending_spawns} queued"
        elif game.status is GameStatus.WON:
            headline, colour, detail = "Victory", GOOD, "all waves defended"
        else:
            headline, colour, detail = "Defeat", DANGER, "the base was overrun"
        self.screen.blit(self.font.render(headline, True, colour), (panel.x + 14, y))
        y += 22
        self.screen.blit(
            self.font_small.render(detail, True, TEXT_DIM), (panel.x + 14, y)
        )
        y += 20
        wave = (
            game.current_wave()
            if game.status is GameStatus.BUILDING
            else game.next_wave()
        )
        if wave is not None:
            label = "Incoming:" if game.status is GameStatus.BUILDING else "Then:"
            self.screen.blit(
                self.font_small.render(label, True, TEXT_DIM), (panel.x + 14, y)
            )
            y += 16
            for line in _wrap(wave.summary(), self.font_small, panel.width - 28):
                self.screen.blit(
                    self.font_small.render(line, True, TEXT), (panel.x + 14, y)
                )
                y += 15
        y += 4
        button = pygame.Rect(panel.x + 14, y, panel.width - 28, 30)
        self.buttons.append(
            Button(
                button,
                "Send next wave" if not game.wave_in_progress else "Wave in progress",
                "next_wave",
                enabled=not game.wave_in_progress and not game.is_over,
                accent=not game.wave_in_progress,
            )
        )
        return y + 40

    def _draw_shop(self, panel: pygame.Rect, y: int) -> int:
        assert self.screen is not None
        self.screen.blit(self.font.render("Towers", True, ACCENT), (panel.x + 14, y))
        y += 24
        for number, (key, kind) in enumerate(TOWER_KINDS.items(), start=1):
            rect = pygame.Rect(panel.x + 14, y, panel.width - 28, 40)
            selected = self.shop_selection == key
            affordable = self.game.gold >= kind.cost
            fill = PANEL_LIGHT if selected else PANEL
            pygame.draw.rect(self.screen, fill, rect, border_radius=7)
            pygame.draw.rect(
                self.screen,
                ACCENT if selected else GRID_LINE,
                rect,
                width=2,
                border_radius=7,
            )
            icon = self.assets.scaled(kind.sprite, 30, TOWER_TINTS.get(key))
            if icon is not None:
                self.screen.blit(icon, (rect.x + 6, rect.y + 6))
            name = self.font_small.render(f"{number}. {kind.name}", True, TEXT)
            self.screen.blit(name, (rect.x + 42, rect.y + 6))
            cost = self.font_small.render(
                f"{kind.cost}g", True, GOLD if affordable else DANGER
            )
            self.screen.blit(cost, (rect.right - cost.get_width() - 8, rect.y + 6))
            base = kind.tier(0)
            tags = []
            if not kind.can_hit_air:
                tags.append("grd")
            if not kind.can_hit_ground:
                tags.append("air")
            if kind.splash_radius:
                tags.append("aoe")
            if kind.slow_factor < 1:
                tags.append("slow")
            summary = f"{base.damage:.0f}dmg {base.fire_rate:.1f}/s"
            if tags:
                summary += " " + " ".join(tags)
            self.screen.blit(
                self.font_small.render(summary, True, TEXT_DIM),
                (rect.x + 42, rect.y + 23),
            )
            # The card above already drew itself, so this is only a hit area.
            self.buttons.append(Button(rect, "", f"shop:{key}", visible=False))
            y += 44
        return y + 4

    def _draw_selection(self, panel: pygame.Rect, y: int) -> int:
        assert self.screen is not None
        tower = self.game.tower_at(self.selected_tile) if self.selected_tile else None
        if tower is None:
            hint = (
                "Click a plot to build."
                if self.shop_selection
                else "Click a tower to inspect it."
            )
            self.screen.blit(
                self.font_small.render(hint, True, TEXT_DIM), (panel.x + 14, y)
            )
            return y + 22
        pygame.draw.line(
            self.screen, GRID_LINE, (panel.x + 14, y), (panel.right - 14, y)
        )
        y += 10
        self.screen.blit(
            self.font.render(f"{tile_label(tower.tile)} · {tower.label}", True, ACCENT),
            (panel.x + 14, y),
        )
        y += 22
        rows = [
            f"damage {tower.damage:.0f}   rate {tower.stats.fire_rate:.1f}/s",
            f"range {tower.range:.0f}   targets {tower.target_mode.value}",
            f"kills {tower.kills}   dealt {tower.damage_dealt:.0f}",
        ]
        for line in rows:
            self.screen.blit(
                self.font_small.render(line, True, TEXT_DIM), (panel.x + 14, y)
            )
            y += 16
        y += 6
        upgrade_cost = tower.kind.upgrade_cost(tower.tier)
        half = (panel.width - 34) // 2
        self.buttons.append(
            Button(
                pygame.Rect(panel.x + 14, y, half, 28),
                f"Upgrade {upgrade_cost}g" if upgrade_cost else "Max tier",
                "upgrade",
                enabled=upgrade_cost is not None and self.game.gold >= upgrade_cost,
                accent=True,
            )
        )
        self.buttons.append(
            Button(
                pygame.Rect(panel.x + 20 + half, y, half, 28),
                f"Sell {tower.sell_value}g",
                "sell",
            )
        )
        y += 34
        self.buttons.append(
            Button(
                pygame.Rect(panel.x + 14, y, panel.width - 28, 26),
                f"Target: {tower.target_mode.value}",
                "target",
            )
        )
        return y + 34

    def _draw_footer(self, panel: pygame.Rect) -> None:
        assert self.screen is not None
        if self.message and self.message_timer > 0:
            lines = _wrap(self.message, self.font_small, panel.width - 28)[:3]
            y = panel.bottom - 82 - len(lines) * 15
            for line in lines:
                self.screen.blit(
                    self.font_small.render(line, True, ACCENT), (panel.x + 14, y)
                )
                y += 15
        y = panel.bottom - 74
        third = (panel.width - 44) // 3
        for offset, (label, action) in enumerate(
            (
                ("Pause" if not self.paused else "Play", "pause"),
                (f"{SPEEDS[self.speed_index]:g}x", "speed"),
                ("Restart", "restart"),
            )
        ):
            self.buttons.append(
                Button(
                    pygame.Rect(panel.x + 14 + offset * (third + 8), y, third, 26),
                    label,
                    action,
                )
            )
        self.buttons.append(
            Button(
                pygame.Rect(panel.x + 14, y + 32, panel.width - 28, 26),
                f"Next level ({self.level_index + 1}/{len(self.level_paths)})",
                "next_level",
            )
        )
        hint = self.font_small.render("F1 controls", True, TEXT_DIM)
        self.screen.blit(hint, (panel.x + 14, panel.bottom - 16))
        if self.assets.missing:
            warn = self.font_small.render(
                f"{len(self.assets.missing)} assets missing", True, DANGER
            )
            self.screen.blit(
                warn, (panel.right - warn.get_width() - 14, panel.bottom - 16)
            )

    def _draw_verdict(self) -> None:
        assert self.screen is not None
        board = pygame.Rect(
            self.board_origin[0],
            self.board_origin[1],
            self.level.width,
            self.level.height,
        )
        shade = pygame.Surface(board.size, pygame.SRCALPHA)
        shade.fill((10, 12, 20, 190))
        self.screen.blit(shade, board.topleft)
        won = self.game.status is GameStatus.WON
        title = self.font_big.render(
            "Victory!" if won else "The base fell", True, GOOD if won else DANGER
        )
        self.screen.blit(
            title, title.get_rect(center=(board.centerx, board.centery - 50))
        )
        lines = [
            f"waves survived: {self.game.wave_index}/{self.game.total_waves}",
            f"enemies destroyed: {self.game.killed}   leaked: {self.game.leaked}",
            f"score: {self.game.score}   time: {self.game.elapsed:.0f}s",
            "R to retry · N for the next level",
        ]
        y = board.centery - 8
        for line in lines:
            text = self.font.render(line, True, TEXT)
            self.screen.blit(text, text.get_rect(center=(board.centerx, y)))
            y += 26

    def _draw_help(self) -> None:
        assert self.screen is not None
        width, height = 430, 40 + len(CONTROLS) * 22
        box = pygame.Rect(0, 0, width, height)
        box.center = (
            self.board_origin[0] + self.level.width // 2,
            self.board_origin[1] + self.level.height // 2,
        )
        pygame.draw.rect(self.screen, (18, 20, 30), box, border_radius=10)
        pygame.draw.rect(self.screen, ACCENT, box, width=2, border_radius=10)
        self.screen.blit(
            self.font.render("Controls", True, ACCENT), (box.x + 16, box.y + 12)
        )
        y = box.y + 38
        for key, description in CONTROLS:
            self.screen.blit(self.font_mono.render(key, True, TEXT), (box.x + 16, y))
            self.screen.blit(
                self.font_small.render(description, True, TEXT_DIM), (box.x + 180, y)
            )
            y += 22


def _enemy_key(name: str) -> str:
    """Map an enemy's display name back to its catalogue key."""
    for key, kind in ENEMY_KINDS.items():
        if kind.name == name:
            return key
    return "grunt"


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
    parser = argparse.ArgumentParser(description="Pygame tower defense")
    parser.add_argument("--level", type=int, default=1, help="level number to start on")
    parser.add_argument(
        "--list-levels", action="store_true", help="print the level list and exit"
    )
    parser.add_argument("--seed", type=int, default=None, help="seed the engine's RNG")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = discover_levels()
    if not paths:
        print("No level files found in levels/.", file=sys.stderr)
        return 1
    if args.list_levels:
        for index, path in enumerate(paths, start=1):
            level = Level.load(path)
            print(f"{index}. {level.name} — {len(level.waves)} waves")
        return 0
    return TowerDefenseApp(paths, index=args.level - 1, seed=args.seed).run()


if __name__ == "__main__":
    raise SystemExit(main())
