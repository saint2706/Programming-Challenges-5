"""Tower defense simulation — rules, economy and combat, with no renderer.

Enemies walk a fixed waypoint path baked into the level; towers occupy build
plots beside it and shoot whatever comes into range. The whole simulation is
advanced by :meth:`TowerDefenseGame.step` in fixed ticks, which makes it
deterministic: the same level, the same build orders and the same tick count
always produce the same result. That is what lets the Pygame front-end, the
tick-based terminal front-end and the test suite share one engine.

Nothing in this module imports Pygame.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

#: Length of one simulation tick, in seconds. 60 Hz keeps the maths stable.
TICK = 1.0 / 60.0
#: Seconds of calm between a cleared wave and the next automatic spawn.
DEFAULT_WAVE_BREAK = 8.0
#: Fraction of the gold spent on a tower that selling returns.
SELL_REFUND = 0.6


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Vec2:
    """An immutable 2D vector in world (pixel) space."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def distance_to(self, other: Vec2) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def normalised(self) -> Vec2:
        length = self.length()
        return Vec2(self.x / length, self.y / length) if length else Vec2()

    def angle_degrees(self) -> float:
        """Heading in degrees, measured clockwise from straight up.

        Sprites in the art pack point upwards, so this is the rotation to apply.
        """
        return math.degrees(math.atan2(self.x, -self.y))

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class Route:
    """A polyline the enemies follow, with distance-based lookup.

    Named ``Route`` rather than ``Path`` to leave :class:`pathlib.Path` alone.
    """

    def __init__(self, points: Sequence[Vec2]) -> None:
        if len(points) < 2:
            raise ValueError("a path needs at least two waypoints")
        self.points = list(points)
        self.segment_lengths = [
            self.points[i].distance_to(self.points[i + 1])
            for i in range(len(self.points) - 1)
        ]
        self.length = sum(self.segment_lengths)

    def position_at(self, distance: float) -> Vec2:
        """Point ``distance`` along the path, clamped to both ends."""
        if distance <= 0:
            return self.points[0]
        if distance >= self.length:
            return self.points[-1]
        remaining = distance
        for index, segment in enumerate(self.segment_lengths):
            if remaining <= segment:
                start, end = self.points[index], self.points[index + 1]
                return start + (end - start) * (remaining / segment)
            remaining -= segment
        return self.points[-1]

    def heading_at(self, distance: float) -> Vec2:
        """Unit direction of travel at ``distance`` along the path."""
        remaining = max(0.0, distance)
        for index, segment in enumerate(self.segment_lengths):
            if remaining <= segment or index == len(self.segment_lengths) - 1:
                return (self.points[index + 1] - self.points[index]).normalised()
            remaining -= segment
        return Vec2(1, 0)


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------
class TargetMode(str, Enum):
    """How a tower picks between the enemies inside its range."""

    FIRST = "first"  # furthest along the path — the default
    LAST = "last"
    CLOSEST = "closest"
    STRONGEST = "strongest"


@dataclass(frozen=True)
class TowerTier:
    """One upgrade step of a tower: what it costs and what it improves."""

    cost: int
    damage: float
    fire_rate: float
    range: float
    label: str = ""


@dataclass(frozen=True)
class TowerKind:
    """A buildable tower archetype."""

    key: str
    name: str
    #: Tier 0 is the base build; later entries are upgrades.
    tiers: tuple[TowerTier, ...]
    projectile_speed: float = 420.0
    #: Radius of splash damage on impact; ``0`` means single-target.
    splash_radius: float = 0.0
    #: Multiplier applied to an enemy's speed when hit (``1.0`` = no slow).
    slow_factor: float = 1.0
    slow_duration: float = 0.0
    #: Flat armour ignored on hit, for towers meant to punch through tanks.
    armour_pierce: float = 0.0
    can_hit_air: bool = True
    can_hit_ground: bool = True
    sprite: str = "turret_cannon"
    description: str = ""

    @property
    def cost(self) -> int:
        return self.tiers[0].cost

    @property
    def max_tier(self) -> int:
        return len(self.tiers) - 1

    def tier(self, index: int) -> TowerTier:
        return self.tiers[max(0, min(index, self.max_tier))]

    def upgrade_cost(self, current_tier: int) -> int | None:
        """Gold to reach the next tier, or ``None`` when fully upgraded."""
        if current_tier >= self.max_tier:
            return None
        return self.tiers[current_tier + 1].cost


@dataclass(frozen=True)
class EnemyKind:
    """An attacking unit archetype."""

    key: str
    name: str
    hp: float
    speed: float
    bounty: int
    #: Flat damage reduction per hit; a hit always does at least 1.
    armour: float = 0.0
    #: Lives lost when this enemy reaches the exit.
    leak_damage: int = 1
    flying: bool = False
    sprite: str = "enemy_grunt"
    description: str = ""


#: The buildable towers, in shop order.
TOWER_KINDS: dict[str, TowerKind] = {
    "gun": TowerKind(
        key="gun",
        name="Gun Turret",
        tiers=(
            TowerTier(cost=60, damage=9, fire_rate=1.6, range=120, label="Mk I"),
            TowerTier(cost=55, damage=15, fire_rate=2.0, range=135, label="Mk II"),
            TowerTier(cost=95, damage=24, fire_rate=2.4, range=150, label="Mk III"),
        ),
        sprite="turret_cannon",
        description="Cheap, reliable single-target damage.",
    ),
    "gatling": TowerKind(
        key="gatling",
        name="Gatling",
        tiers=(
            TowerTier(cost=110, damage=5, fire_rate=6.0, range=105, label="Mk I"),
            TowerTier(cost=100, damage=7, fire_rate=8.0, range=115, label="Mk II"),
            TowerTier(cost=160, damage=9, fire_rate=11.0, range=125, label="Mk III"),
        ),
        projectile_speed=620.0,
        sprite="turret_gatling",
        description="Shreds fast, lightly armoured swarms.",
    ),
    "frost": TowerKind(
        key="frost",
        name="Frost Tower",
        tiers=(
            TowerTier(cost=90, damage=4, fire_rate=1.2, range=115, label="Chill"),
            TowerTier(cost=85, damage=6, fire_rate=1.5, range=130, label="Freeze"),
            TowerTier(
                cost=140, damage=9, fire_rate=1.8, range=145, label="Deep Freeze"
            ),
        ),
        projectile_speed=340.0,
        slow_factor=0.55,
        slow_duration=2.0,
        sprite="turret_frost",
        description="Little damage, but halves enemy speed.",
    ),
    "mortar": TowerKind(
        key="mortar",
        name="Mortar",
        tiers=(
            TowerTier(cost=150, damage=26, fire_rate=0.55, range=185, label="Mk I"),
            TowerTier(cost=140, damage=40, fire_rate=0.7, range=200, label="Mk II"),
            TowerTier(cost=220, damage=62, fire_rate=0.85, range=220, label="Mk III"),
        ),
        projectile_speed=300.0,
        splash_radius=52.0,
        armour_pierce=3.0,
        can_hit_air=False,
        sprite="turret_mortar",
        description="Slow splash damage. Cannot hit aircraft.",
    ),
    "flak": TowerKind(
        key="flak",
        name="Flak Battery",
        tiers=(
            TowerTier(cost=120, damage=14, fire_rate=2.2, range=160, label="Mk I"),
            TowerTier(cost=110, damage=22, fire_rate=2.6, range=175, label="Mk II"),
            TowerTier(cost=175, damage=34, fire_rate=3.0, range=190, label="Mk III"),
        ),
        projectile_speed=700.0,
        splash_radius=26.0,
        can_hit_ground=False,
        sprite="turret_flak",
        description="Anti-air only, but the best answer to bombers.",
    ),
}

#: The attacking units levels can schedule.
ENEMY_KINDS: dict[str, EnemyKind] = {
    "grunt": EnemyKind(
        key="grunt",
        name="Grunt",
        hp=45,
        speed=52,
        bounty=8,
        sprite="enemy_grunt",
        description="Baseline ground unit.",
    ),
    "runner": EnemyKind(
        key="runner",
        name="Runner",
        hp=28,
        speed=104,
        bounty=9,
        sprite="enemy_runner",
        description="Fragile but very fast — slow it down.",
    ),
    "armoured": EnemyKind(
        key="armoured",
        name="Armoured Car",
        hp=95,
        speed=44,
        bounty=16,
        armour=4,
        sprite="enemy_armoured",
        description="Shrugs off small-calibre fire.",
    ),
    "bomber": EnemyKind(
        key="bomber",
        name="Bomber",
        hp=70,
        speed=88,
        bounty=20,
        flying=True,
        sprite="enemy_flyer",
        description="Flies straight to the exit; only AA can touch it.",
    ),
    "juggernaut": EnemyKind(
        key="juggernaut",
        name="Juggernaut",
        hp=620,
        speed=30,
        bounty=110,
        armour=9,
        leak_damage=6,
        sprite="enemy_boss",
        description="Wave boss. Heavily armoured and it hurts to leak.",
    ),
}


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SpawnGroup:
    """A run of identical enemies inside a wave."""

    enemy: str
    count: int
    #: Seconds between each spawn in the group.
    interval: float = 0.8
    #: Seconds after the wave starts before the first spawn.
    delay: float = 0.0
    #: Multiplies the archetype's HP, for scaling late waves.
    hp_scale: float = 1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpawnGroup:
        if data["enemy"] not in ENEMY_KINDS:
            raise ValueError(f"unknown enemy {data['enemy']!r}")
        return cls(
            enemy=data["enemy"],
            count=int(data.get("count", 1)),
            interval=float(data.get("interval", 0.8)),
            delay=float(data.get("delay", 0.0)),
            hp_scale=float(data.get("hp_scale", 1.0)),
        )

    @property
    def duration(self) -> float:
        """Seconds from wave start until this group's last spawn."""
        return self.delay + max(0, self.count - 1) * self.interval


@dataclass(frozen=True)
class Wave:
    """One numbered wave: its groups and the bonus for clearing it."""

    groups: tuple[SpawnGroup, ...]
    reward: int = 25
    name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Wave:
        return cls(
            groups=tuple(SpawnGroup.from_dict(g) for g in data["groups"]),
            reward=int(data.get("reward", 25)),
            name=str(data.get("name", "")),
        )

    @property
    def total_enemies(self) -> int:
        return sum(group.count for group in self.groups)

    def summary(self) -> str:
        """Short human-readable composition, e.g. ``6x Grunt, 2x Runner``."""
        return ", ".join(f"{g.count}x {ENEMY_KINDS[g.enemy].name}" for g in self.groups)


@dataclass
class Level:
    """A playable map: geometry, build plots, economy and wave schedule."""

    name: str
    cols: int
    rows: int
    tile_size: int
    #: Waypoints in *tile* coordinates; converted to tile centres on load.
    waypoints: tuple[tuple[int, int], ...]
    plots: tuple[tuple[int, int], ...]
    waves: tuple[Wave, ...]
    starting_gold: int = 220
    starting_lives: int = 20
    wave_break: float = DEFAULT_WAVE_BREAK
    description: str = ""
    #: Purely cosmetic props: ``(tile_x, tile_y, sprite_name)``.
    decor: tuple[tuple[int, int, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.plots:
            raise ValueError("a level needs at least one build plot")
        path_tiles = set(self.path_tiles())
        clashes = sorted(set(self.plots) & path_tiles)
        if clashes:
            raise ValueError(f"build plots sit on the path: {clashes}")
        for tile in self.plots:
            if not self.in_bounds(*tile):
                raise ValueError(f"build plot {tile} is off the map")
        for tile in self.waypoints:
            if not self.in_bounds(*tile):
                raise ValueError(f"waypoint {tile} is off the map")

    # -- geometry -------------------------------------------------------
    @property
    def width(self) -> int:
        return self.cols * self.tile_size

    @property
    def height(self) -> int:
        return self.rows * self.tile_size

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def tile_centre(self, col: int, row: int) -> Vec2:
        half = self.tile_size / 2
        return Vec2(col * self.tile_size + half, row * self.tile_size + half)

    def tile_at(self, position: Vec2) -> tuple[int, int]:
        return (int(position.x // self.tile_size), int(position.y // self.tile_size))

    def ground_path(self) -> Route:
        """The waypoint polyline, in world coordinates."""
        return Route([self.tile_centre(col, row) for col, row in self.waypoints])

    def air_path(self) -> Route:
        """Aircraft fly straight from the entry tile to the exit tile."""
        start = self.tile_centre(*self.waypoints[0])
        end = self.tile_centre(*self.waypoints[-1])
        return Route([start, end])

    def path_tiles(self) -> Iterator[tuple[int, int]]:
        """Every tile the ground path crosses, walking waypoint to waypoint.

        Consecutive waypoints must share a row or a column, which keeps the road
        drawable as whole tiles in both front-ends.
        """
        for (c0, r0), (c1, r1) in zip(self.waypoints, self.waypoints[1:]):
            if c0 != c1 and r0 != r1:
                raise ValueError(
                    f"waypoints {(c0, r0)} -> {(c1, r1)} are diagonal; "
                    "use an intermediate waypoint"
                )
            step_c = (c1 > c0) - (c1 < c0)
            step_r = (r1 > r0) - (r1 < r0)
            col, row = c0, r0
            yield (col, row)
            while (col, row) != (c1, r1):
                col += step_c
                row += step_r
                yield (col, row)

    # -- loading --------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Level:
        return cls(
            name=str(data.get("name", "Unnamed")),
            cols=int(data["cols"]),
            rows=int(data["rows"]),
            tile_size=int(data.get("tile_size", 48)),
            waypoints=tuple((int(p[0]), int(p[1])) for p in data["waypoints"]),
            plots=tuple((int(p[0]), int(p[1])) for p in data["plots"]),
            waves=tuple(Wave.from_dict(w) for w in data["waves"]),
            starting_gold=int(data.get("starting_gold", 220)),
            starting_lives=int(data.get("starting_lives", 20)),
            wave_break=float(data.get("wave_break", DEFAULT_WAVE_BREAK)),
            description=str(data.get("description", "")),
            decor=tuple(
                (int(d[0]), int(d[1]), str(d[2])) for d in data.get("decor", ())
            ),
        )

    @classmethod
    def load(cls, path: str | Path) -> Level:
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))


def discover_levels(directory: str | Path | None = None) -> list[Path]:
    """Sorted list of level JSON files shipped with the challenge."""
    folder = (
        Path(directory) if directory else Path(__file__).resolve().parent / "levels"
    )
    return sorted(folder.glob("*.json"))


# ---------------------------------------------------------------------------
# Live entities
# ---------------------------------------------------------------------------
@dataclass
class Enemy:
    """One attacking unit walking its path."""

    kind: EnemyKind
    max_hp: float
    hp: float
    path: Route
    distance: float = 0.0
    #: Remaining seconds of slow, and the factor being applied.
    slow_timer: float = 0.0
    slow_factor: float = 1.0
    alive: bool = True
    leaked: bool = False
    position: Vec2 = field(default_factory=Vec2)
    heading: Vec2 = field(default_factory=lambda: Vec2(1, 0))

    @property
    def speed(self) -> float:
        return self.kind.speed * (self.slow_factor if self.slow_timer > 0 else 1.0)

    @property
    def hp_fraction(self) -> float:
        return max(0.0, self.hp / self.max_hp) if self.max_hp else 0.0

    @property
    def progress(self) -> float:
        """How far along the path this enemy is, from 0 to 1."""
        return min(1.0, self.distance / self.path.length) if self.path.length else 1.0

    def refresh_position(self) -> None:
        self.position = self.path.position_at(self.distance)
        self.heading = self.path.heading_at(self.distance)

    def advance(self, dt: float) -> bool:
        """Move along the path. Returns ``True`` when the exit is reached."""
        if self.slow_timer > 0:
            self.slow_timer = max(0.0, self.slow_timer - dt)
            if self.slow_timer == 0:
                self.slow_factor = 1.0
        self.distance += self.speed * dt
        self.refresh_position()
        return self.distance >= self.path.length

    def apply_slow(self, factor: float, duration: float) -> None:
        """Apply a slow, keeping whichever effect is harsher."""
        if factor >= 1.0 or duration <= 0:
            return
        if self.slow_timer <= 0 or factor < self.slow_factor:
            self.slow_factor = factor
        self.slow_timer = max(self.slow_timer, duration)

    def take_damage(self, amount: float, armour_pierce: float = 0.0) -> float:
        """Damage the enemy after armour, returning the amount actually dealt."""
        effective_armour = max(0.0, self.kind.armour - armour_pierce)
        dealt = max(1.0, amount - effective_armour)
        dealt = min(dealt, self.hp)
        self.hp -= dealt
        if self.hp <= 0:
            self.alive = False
        return dealt


@dataclass
class Tower:
    """A built tower sitting on one plot."""

    kind: TowerKind
    tile: tuple[int, int]
    position: Vec2
    tier: int = 0
    cooldown: float = 0.0
    #: Gold sunk into this tower, which sets the sell price.
    invested: int = 0
    angle: float = 0.0
    target_mode: TargetMode = TargetMode.FIRST
    kills: int = 0
    damage_dealt: float = 0.0

    @property
    def stats(self) -> TowerTier:
        return self.kind.tier(self.tier)

    @property
    def range(self) -> float:
        return self.stats.range

    @property
    def damage(self) -> float:
        return self.stats.damage

    @property
    def fire_interval(self) -> float:
        return 1.0 / self.stats.fire_rate

    @property
    def sell_value(self) -> int:
        return int(self.invested * SELL_REFUND)

    @property
    def label(self) -> str:
        tier_label = self.stats.label or f"T{self.tier + 1}"
        return f"{self.kind.name} ({tier_label})"

    def can_target(self, enemy: Enemy) -> bool:
        if enemy.kind.flying and not self.kind.can_hit_air:
            return False
        if not enemy.kind.flying and not self.kind.can_hit_ground:
            return False
        return self.position.distance_to(enemy.position) <= self.range

    def pick_target(self, enemies: Iterable[Enemy]) -> Enemy | None:
        """Best target in range according to :attr:`target_mode`."""
        candidates = [e for e in enemies if e.alive and self.can_target(e)]
        if not candidates:
            return None
        if self.target_mode is TargetMode.FIRST:
            return max(candidates, key=lambda e: e.distance)
        if self.target_mode is TargetMode.LAST:
            return min(candidates, key=lambda e: e.distance)
        if self.target_mode is TargetMode.CLOSEST:
            return min(candidates, key=lambda e: self.position.distance_to(e.position))
        return max(candidates, key=lambda e: e.hp)


@dataclass
class Projectile:
    """A shot in flight, homing on the enemy it was fired at."""

    position: Vec2
    target: Enemy
    speed: float
    damage: float
    splash_radius: float = 0.0
    slow_factor: float = 1.0
    slow_duration: float = 0.0
    armour_pierce: float = 0.0
    owner: Tower | None = None
    alive: bool = True
    angle: float = 0.0
    sprite: str = "bullet"

    def advance(self, dt: float) -> bool:
        """Fly toward the target. Returns ``True`` on impact."""
        if not self.target.alive:
            # The target died mid-flight; the shot is wasted.
            self.alive = False
            return False
        offset = self.target.position - self.position
        distance = offset.length()
        travel = self.speed * dt
        self.angle = offset.angle_degrees()
        if distance <= travel:
            self.position = self.target.position
            return True
        self.position = self.position + offset.normalised() * travel
        return False


class GameStatus(str, Enum):
    """Overall state of a run."""

    BUILDING = "building"  # between waves; build freely
    WAVE = "wave"  # a wave is on the field
    WON = "won"
    LOST = "lost"


class BuildError(ValueError):
    """Raised when a build, upgrade or sell request is not allowed."""


@dataclass
class GameEvent:
    """Something the front-ends may want to render or play a sound for."""

    kind: str  # "shoot" | "hit" | "kill" | "leak" | "build" | "wave" | "end"
    position: Vec2 = field(default_factory=Vec2)
    detail: str = ""


class TowerDefenseGame:
    """The simulation: towers, enemies, projectiles, gold, lives and waves."""

    def __init__(self, level: Level, seed: int | None = None) -> None:
        self.level = level
        self.rng = random.Random(seed)
        self.ground_path = level.ground_path()
        self.air_path = level.air_path()
        self.plots: set[tuple[int, int]] = set(level.plots)
        self.towers: dict[tuple[int, int], Tower] = {}
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.gold = level.starting_gold
        self.lives = level.starting_lives
        self.score = 0
        self.wave_index = 0
        self.status = GameStatus.BUILDING
        self.elapsed = 0.0
        #: Countdown to the next automatic wave while :attr:`status` is BUILDING.
        self.break_timer = level.wave_break
        self.leaked = 0
        self.killed = 0
        #: Events produced since the last :meth:`drain_events` call.
        self.events: list[GameEvent] = []
        self._spawn_plan: list[tuple[float, SpawnGroup]] = []
        self._wave_clock = 0.0

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @property
    def wave_number(self) -> int:
        """1-based number of the wave in progress, or the next one."""
        return min(self.wave_index + 1, len(self.level.waves))

    @property
    def total_waves(self) -> int:
        return len(self.level.waves)

    @property
    def is_over(self) -> bool:
        return self.status in (GameStatus.WON, GameStatus.LOST)

    @property
    def wave_in_progress(self) -> bool:
        return self.status is GameStatus.WAVE

    @property
    def pending_spawns(self) -> int:
        """Enemies of the current wave still queued to appear."""
        return len(self._spawn_plan)

    @property
    def alive_enemies(self) -> int:
        return sum(1 for enemy in self.enemies if enemy.alive)

    def current_wave(self) -> Wave | None:
        """The wave being fought, or the next one while building."""
        if self.wave_index >= len(self.level.waves):
            return None
        return self.level.waves[self.wave_index]

    def next_wave(self) -> Wave | None:
        """The wave after the current one, for a UI preview."""
        following = self.wave_index + (1 if self.status is GameStatus.WAVE else 0)
        if following >= len(self.level.waves):
            return None
        return self.level.waves[following]

    def tower_at(self, tile: tuple[int, int]) -> Tower | None:
        return self.towers.get(tile)

    def is_buildable(self, tile: tuple[int, int]) -> bool:
        return tile in self.plots and tile not in self.towers

    def drain_events(self) -> list[GameEvent]:
        """Take the accumulated events, clearing the queue."""
        events, self.events = self.events, []
        return events

    def stats(self) -> dict[str, Any]:
        """Snapshot for HUDs and end-of-run summaries."""
        return {
            "level": self.level.name,
            "status": self.status.value,
            "wave": self.wave_number,
            "total_waves": self.total_waves,
            "gold": self.gold,
            "lives": self.lives,
            "score": self.score,
            "towers": len(self.towers),
            "enemies": sum(1 for e in self.enemies if e.alive),
            "killed": self.killed,
            "leaked": self.leaked,
            "elapsed": round(self.elapsed, 2),
        }

    # ------------------------------------------------------------------
    # Build / upgrade / sell
    # ------------------------------------------------------------------
    def build(self, tile: tuple[int, int], kind_key: str) -> Tower:
        """Place a tower. Raises :class:`BuildError` if it is not allowed."""
        if self.is_over:
            raise BuildError("the run is over")
        kind = TOWER_KINDS.get(kind_key)
        if kind is None:
            raise BuildError(f"unknown tower {kind_key!r}")
        if tile not in self.plots:
            raise BuildError(f"{_tile_name(tile)} is not a build plot")
        if tile in self.towers:
            raise BuildError(f"{_tile_name(tile)} already has a tower")
        if self.gold < kind.cost:
            raise BuildError(f"need {kind.cost} gold, you have {self.gold}")
        self.gold -= kind.cost
        tower = Tower(
            kind=kind,
            tile=tile,
            position=self.level.tile_centre(*tile),
            invested=kind.cost,
        )
        self.towers[tile] = tower
        self.events.append(GameEvent("build", tower.position, kind.name))
        return tower

    def upgrade(self, tile: tuple[int, int]) -> Tower:
        """Advance a tower one tier."""
        tower = self.towers.get(tile)
        if tower is None:
            raise BuildError(f"no tower at {_tile_name(tile)}")
        cost = tower.kind.upgrade_cost(tower.tier)
        if cost is None:
            raise BuildError(f"{tower.kind.name} is already fully upgraded")
        if self.gold < cost:
            raise BuildError(f"need {cost} gold, you have {self.gold}")
        self.gold -= cost
        tower.tier += 1
        tower.invested += cost
        self.events.append(GameEvent("build", tower.position, tower.label))
        return tower

    def sell(self, tile: tuple[int, int]) -> int:
        """Remove a tower and refund part of its cost. Returns the refund."""
        tower = self.towers.get(tile)
        if tower is None:
            raise BuildError(f"no tower at {_tile_name(tile)}")
        refund = tower.sell_value
        self.gold += refund
        del self.towers[tile]
        # Shots already in the air lose their owner but still land.
        self.events.append(
            GameEvent("build", tower.position, f"sold {tower.kind.name}")
        )
        return refund

    def set_target_mode(self, tile: tuple[int, int], mode: TargetMode | str) -> Tower:
        """Change which enemy a tower prefers."""
        tower = self.towers.get(tile)
        if tower is None:
            raise BuildError(f"no tower at {_tile_name(tile)}")
        tower.target_mode = TargetMode(mode)
        return tower

    # ------------------------------------------------------------------
    # Waves
    # ------------------------------------------------------------------
    def start_wave(self) -> Wave:
        """Send the next wave immediately. Raises if one is already running."""
        if self.is_over:
            raise BuildError("the run is over")
        if self.status is GameStatus.WAVE:
            raise BuildError("a wave is already on the field")
        wave = self.current_wave()
        if wave is None:
            raise BuildError("no waves left")
        self._spawn_plan = []
        for group in wave.groups:
            for n in range(group.count):
                self._spawn_plan.append((group.delay + n * group.interval, group))
        self._spawn_plan.sort(key=lambda item: item[0])
        self._wave_clock = 0.0
        self.status = GameStatus.WAVE
        self.events.append(
            GameEvent("wave", detail=f"Wave {self.wave_number}: {wave.summary()}")
        )
        return wave

    def _spawn(self, group: SpawnGroup) -> Enemy:
        kind = ENEMY_KINDS[group.enemy]
        hp = kind.hp * group.hp_scale
        path = self.air_path if kind.flying else self.ground_path
        enemy = Enemy(kind=kind, max_hp=hp, hp=hp, path=path)
        enemy.refresh_position()
        self.enemies.append(enemy)
        return enemy

    def _finish_wave(self) -> None:
        """Award the clear bonus and move to the next wave (or win)."""
        wave = self.level.waves[self.wave_index]
        self.gold += wave.reward
        self.score += wave.reward
        self.wave_index += 1
        self.events.append(
            GameEvent("wave", detail=f"Wave cleared — +{wave.reward} gold")
        )
        if self.wave_index >= len(self.level.waves):
            self.status = GameStatus.WON
            self.events.append(GameEvent("end", detail="All waves defended!"))
        else:
            self.status = GameStatus.BUILDING
            self.break_timer = self.level.wave_break

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def step(self, dt: float = TICK) -> None:
        """Advance the simulation by ``dt`` seconds."""
        if self.is_over:
            return
        self.elapsed += dt
        if self.status is GameStatus.BUILDING:
            self.break_timer -= dt
            if self.break_timer <= 0:
                self.start_wave()
            return

        self._wave_clock += dt
        self._release_spawns()
        self._move_enemies(dt)
        self._fire_towers(dt)
        self._move_projectiles(dt)
        self._reap()
        self._check_wave_end()

    def run_ticks(self, ticks: int, dt: float = TICK) -> None:
        """Advance a whole number of fixed ticks (used by tests and the TUI)."""
        for _ in range(ticks):
            if self.is_over:
                return
            self.step(dt)

    def run_seconds(self, seconds: float, dt: float = TICK) -> None:
        """Advance roughly ``seconds`` of simulation in fixed ticks."""
        self.run_ticks(max(0, round(seconds / dt)), dt)

    def _release_spawns(self) -> None:
        while self._spawn_plan and self._spawn_plan[0][0] <= self._wave_clock:
            _, group = self._spawn_plan.pop(0)
            self._spawn(group)

    def _move_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.advance(dt):
                enemy.alive = False
                enemy.leaked = True
                self.leaked += 1
                self.lives -= enemy.kind.leak_damage
                self.events.append(GameEvent("leak", enemy.position, enemy.kind.name))
                if self.lives <= 0:
                    self.lives = 0
                    self.status = GameStatus.LOST
                    self.events.append(GameEvent("end", detail="Base overrun."))
                    return

    def _fire_towers(self, dt: float) -> None:
        for tower in self.towers.values():
            tower.cooldown = max(0.0, tower.cooldown - dt)
            target = tower.pick_target(self.enemies)
            if target is None:
                continue
            tower.angle = (target.position - tower.position).angle_degrees()
            if tower.cooldown > 0:
                continue
            tower.cooldown = tower.fire_interval
            self.projectiles.append(
                Projectile(
                    position=tower.position,
                    target=target,
                    speed=tower.kind.projectile_speed,
                    damage=tower.damage,
                    splash_radius=tower.kind.splash_radius,
                    slow_factor=tower.kind.slow_factor,
                    slow_duration=tower.kind.slow_duration,
                    armour_pierce=tower.kind.armour_pierce,
                    owner=tower,
                    angle=tower.angle,
                    sprite=_projectile_sprite(tower.kind),
                )
            )
            self.events.append(GameEvent("shoot", tower.position, tower.kind.key))

    def _move_projectiles(self, dt: float) -> None:
        for projectile in self.projectiles:
            if not projectile.alive:
                continue
            if projectile.advance(dt):
                self._impact(projectile)
                projectile.alive = False

    def _impact(self, projectile: Projectile) -> None:
        """Resolve a hit: direct damage, then splash, then slow."""
        hits: list[Enemy] = [projectile.target]
        if projectile.splash_radius > 0:
            hits = [
                enemy
                for enemy in self.enemies
                if enemy.alive
                and enemy.position.distance_to(projectile.position)
                <= projectile.splash_radius
            ]
            if projectile.target not in hits and projectile.target.alive:
                hits.append(projectile.target)
        for enemy in hits:
            if not enemy.alive:
                continue
            dealt = enemy.take_damage(projectile.damage, projectile.armour_pierce)
            enemy.apply_slow(projectile.slow_factor, projectile.slow_duration)
            if projectile.owner is not None:
                projectile.owner.damage_dealt += dealt
            if not enemy.alive:
                self._reward(enemy, projectile.owner)
        self.events.append(GameEvent("hit", projectile.position, projectile.sprite))

    def _reward(self, enemy: Enemy, killer: Tower | None) -> None:
        self.gold += enemy.kind.bounty
        self.score += enemy.kind.bounty
        self.killed += 1
        if killer is not None:
            killer.kills += 1
        self.events.append(GameEvent("kill", enemy.position, enemy.kind.name))

    def _reap(self) -> None:
        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

    def _check_wave_end(self) -> None:
        if self.status is not GameStatus.WAVE:
            return
        if self._spawn_plan or self.enemies:
            return
        self._finish_wave()


def _projectile_sprite(kind: TowerKind) -> str:
    """Sprite name for the shots a tower kind fires."""
    if kind.splash_radius > 0:
        return "rocket" if kind.can_hit_air else "shell"
    if kind.slow_factor < 1.0:
        return "frost_bolt"
    return "bullet"


def _tile_name(tile: tuple[int, int]) -> str:
    """Human-friendly tile label, e.g. ``(2, 5)`` -> ``c6``."""
    col, row = tile
    return f"{chr(ord('a') + col)}{row + 1}" if 0 <= col < 26 else f"({col},{row})"


def parse_tile(text: str) -> tuple[int, int]:
    """Parse ``c6`` or ``2,5`` into ``(col, row)``.

    Raises :class:`ValueError` on anything else, which the terminal front-end
    turns into a friendly message.
    """
    raw = text.strip().lower().replace(" ", "")
    if "," in raw:
        col_text, _, row_text = raw.partition(",")
        return (int(col_text), int(row_text))
    if len(raw) >= 2 and raw[0].isalpha() and raw[1:].isdigit():
        return (ord(raw[0]) - ord("a"), int(raw[1:]) - 1)
    raise ValueError(f"cannot read tile {text!r} — try 'c6' or '2,5'")


def tile_label(tile: tuple[int, int]) -> str:
    """Public alias of the internal tile formatter."""
    return _tile_name(tile)
