"""Tick-based terminal front-end for the tower defense engine.

Real-time tower defense does not translate well to a TTY, so this front-end
turns time into a resource you spend explicitly: you issue build/upgrade/sell
orders, then advance the clock with ``step`` or ``run`` and watch the ASCII map
redraw. Because :mod:`core` is deterministic that makes the terminal version a
faithful, fully reproducible view of the same game the Pygame client plays.

    python terminal.py                     # first level
    python terminal.py --level 2           # pick a level
    python terminal.py --list-levels
    python terminal.py --script demo.txt   # replay a file of commands

Type ``help`` at the prompt for the command list.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from core import (
    TOWER_KINDS,
    BuildError,
    GameStatus,
    Level,
    TargetMode,
    TowerDefenseGame,
    discover_levels,
    parse_tile,
    tile_label,
)

#: Two-character glyph for each tower kind, plus its tier digit.
TOWER_GLYPHS = {"gun": "G", "gatling": "A", "frost": "F", "mortar": "M", "flak": "K"}
#: One-character glyph for each enemy kind (boss is upper-case).
ENEMY_GLYPHS = {
    "grunt": "g",
    "runner": "r",
    "armoured": "a",
    "bomber": "b",
    "juggernaut": "J",
}
DECOR_GLYPHS = {"tree": "^^", "bush": ",,", "rock": "nn"}

COLOURS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "path": "\033[38;5;137m",
    "grass": "\033[38;5;65m",
    "plot": "\033[38;5;250m",
    "tower": "\033[38;5;81m",
    "enemy": "\033[38;5;203m",
    "boss": "\033[38;5;198m",
    "air": "\033[38;5;213m",
    "gold": "\033[38;5;220m",
    "warn": "\033[38;5;209m",
    "good": "\033[38;5;120m",
    "info": "\033[38;5;117m",
}


def disable_colour() -> None:
    for key in COLOURS:
        COLOURS[key] = ""


def c(name: str, text: str) -> str:
    return f"{COLOURS[name]}{text}{COLOURS['reset']}" if COLOURS[name] else text


HELP = """Commands (time only advances when you say so):
  build <tile> <tower>   b c5 gun        place a tower on a build plot
  upgrade <tile>         u c5            advance a tower one tier
  sell <tile>            s c5            remove a tower for a partial refund
  target <tile> <mode>   t c5 closest    first | last | closest | strongest
  wave                   w               send the next wave immediately
  step [seconds]         . 2             advance the clock (default 1 second)
  run [seconds]          r               advance until the wave ends (max 120s)
  map                    m               redraw the map
  towers                                 list your towers and their stats
  shop                                   list tower kinds, costs and stats
  waves                                  list the level's wave schedule
  info <tile>                            describe one tile
  legend                                 explain the map glyphs
  help / quit"""

LEGEND = f"""Map glyphs:
  {"::":<4} road (enemies walk here)     {"..":<4} open ground
  {"[]":<4} empty build plot             {"G1":<4} tower: kind letter + tier
  {">>":<4} entry                        {"<<":<4} exit (leaks cost lives)
  {"^^":<4} tree   {",,":<4} bush   {"nn":<4} rock
  Towers: G gun, A gatling, F frost, M mortar, K flak
  Enemies overlay their tile: g grunt, r runner, a armoured, b bomber, J juggernaut"""


class TerminalGame:
    """Command loop around a :class:`TowerDefenseGame`."""

    def __init__(self, level: Level, seed: int | None = None) -> None:
        self.level = level
        self.game = TowerDefenseGame(level, seed=seed)
        self.path_tiles = set(level.path_tiles())
        self.decor = {(d[0], d[1]): d[2] for d in level.decor}
        self.entry = level.waypoints[0]
        self.exit = level.waypoints[-1]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def enemy_overlay(self) -> dict[tuple[int, int], str]:
        """Glyph per occupied tile; the toughest enemy on a tile wins."""
        overlay: dict[tuple[int, int], tuple[float, str]] = {}
        for enemy in self.game.enemies:
            if not enemy.alive:
                continue
            tile = self.level.tile_at(enemy.position)
            glyph = ENEMY_GLYPHS.get(enemy.kind.key, "e")
            current = overlay.get(tile)
            if current is None or enemy.hp > current[0]:
                overlay[tile] = (enemy.hp, glyph)
        return {tile: glyph for tile, (_, glyph) in overlay.items()}

    def render_map(self) -> str:
        overlay = self.enemy_overlay()
        header = "    " + "".join(
            f"{chr(ord('a') + col):^2}" for col in range(self.level.cols)
        )
        lines = [c("dim", header)]
        for row in range(self.level.rows):
            cells = []
            for col in range(self.level.cols):
                tile = (col, row)
                cells.append(self._cell(tile, overlay.get(tile)))
            lines.append(c("dim", f"{row + 1:>3} ") + "".join(cells))
        return "\n".join(lines)

    def _cell(self, tile: tuple[int, int], enemy_glyph: str | None) -> str:
        tower = self.game.tower_at(tile)
        if enemy_glyph is not None:
            # An enemy hides whatever is under it; a tower keeps its letter.
            style = (
                "boss"
                if enemy_glyph == "J"
                else ("air" if enemy_glyph == "b" else "enemy")
            )
            second = TOWER_GLYPHS.get(tower.kind.key, "?") if tower else enemy_glyph
            return c(style, f"{enemy_glyph}{second}")
        if tower is not None:
            return c(
                "tower", f"{TOWER_GLYPHS.get(tower.kind.key, '?')}{tower.tier + 1}"
            )
        if tile == self.entry:
            return c("warn", ">>")
        if tile == self.exit:
            return c("warn", "<<")
        if tile in self.path_tiles:
            return c("path", "::")
        if tile in self.game.plots:
            return c("plot", "[]")
        if tile in self.decor:
            return c("grass", DECOR_GLYPHS.get(self.decor[tile], "''"))
        return c("grass", "..")

    def render_status(self) -> str:
        game = self.game
        wave = game.current_wave()
        bits = [
            c("gold", f"gold {game.gold}"),
            c("good" if game.lives > 5 else "warn", f"lives {game.lives}"),
            f"wave {game.wave_number}/{game.total_waves}",
            f"t {game.elapsed:6.1f}s",
            f"score {game.score}",
        ]
        line = c("bold", " | ".join(bits))
        if game.status is GameStatus.BUILDING:
            preview = f" — next: {wave.summary()}" if wave else ""
            phase = c(
                "info",
                f"BUILDING — auto-start in {max(0.0, game.break_timer):.1f}s"
                f"{preview}",
            )
        elif game.status is GameStatus.WAVE:
            phase = c(
                "warn",
                f"WAVE {game.wave_number} — {game.alive_enemies} on field, "
                f"{game.pending_spawns} to spawn",
            )
        elif game.status is GameStatus.WON:
            phase = c("good", "VICTORY — every wave defended!")
        else:
            phase = c("warn", "DEFEAT — the base was overrun.")
        return f"{line}\n{phase}"

    def show(self) -> None:
        print()
        print(self.render_map())
        print(self.render_status())

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report_events(self) -> None:
        """Summarise what happened since the last drain."""
        events = self.game.drain_events()
        if not events:
            return
        kills = sum(1 for e in events if e.kind == "kill")
        leaks = [e for e in events if e.kind == "leak"]
        for event in events:
            if event.kind in {"wave", "end"}:
                print(c("info", f"  * {event.detail}"))
        if kills:
            print(c("good", f"  * {kills} enemy(ies) destroyed"))
        for event in leaks:
            print(c("warn", f"  ! {event.detail} reached the exit"))

    def list_towers(self) -> None:
        if not self.game.towers:
            print(c("dim", "  no towers built yet"))
            return
        print(
            c(
                "bold",
                f"  {'tile':<5}{'tower':<22}{'dmg':>6}{'rate':>6}{'rng':>6}{'kills':>7}{'sell':>6}  target",
            )
        )
        for tile, tower in sorted(self.game.towers.items()):
            upgrade = tower.kind.upgrade_cost(tower.tier)
            suffix = f"  (upgrade {upgrade}g)" if upgrade else "  (max)"
            print(
                f"  {tile_label(tile):<5}{tower.label:<22}{tower.damage:>6.0f}"
                f"{tower.stats.fire_rate:>6.1f}{tower.range:>6.0f}"
                f"{tower.kills:>7}{tower.sell_value:>6}  {tower.target_mode.value}{suffix}"
            )

    def list_shop(self) -> None:
        print(
            c(
                "bold",
                f"  {'key':<9}{'name':<15}{'cost':>5}{'dmg':>6}{'rate':>6}{'rng':>6}  notes",
            )
        )
        for key, kind in TOWER_KINDS.items():
            base = kind.tier(0)
            notes = [kind.description]
            if not kind.can_hit_air:
                notes.append("ground only")
            if not kind.can_hit_ground:
                notes.append("air only")
            if kind.splash_radius:
                notes.append(f"splash {kind.splash_radius:.0f}")
            if kind.slow_factor < 1:
                notes.append(f"slow x{kind.slow_factor:.2f}")
            print(
                f"  {key:<9}{kind.name:<15}{base.cost:>5}{base.damage:>6.0f}"
                f"{base.fire_rate:>6.1f}{base.range:>6.0f}  {' · '.join(notes)}"
            )

    def list_waves(self) -> None:
        for index, wave in enumerate(self.level.waves, start=1):
            marker = "->" if index == self.game.wave_number else "  "
            name = f"{wave.name}: " if wave.name else ""
            print(
                f"  {marker} {index:>2}. {name}{wave.summary()}" f"  (+{wave.reward}g)"
            )

    def describe_tile(self, tile: tuple[int, int]) -> None:
        label = tile_label(tile)
        if not self.level.in_bounds(*tile):
            print(c("warn", f"  {label} is off the map"))
            return
        tower = self.game.tower_at(tile)
        if tower is not None:
            upgrade = tower.kind.upgrade_cost(tower.tier)
            print(f"  {label}: {tower.label} — {tower.kind.description}")
            print(
                f"    damage {tower.damage:.0f} · {tower.stats.fire_rate:.1f}/s · "
                f"range {tower.range:.0f} · targets {tower.target_mode.value}"
            )
            print(
                f"    kills {tower.kills} · damage dealt {tower.damage_dealt:.0f} · "
                f"sell for {tower.sell_value}g · "
                + (f"upgrade for {upgrade}g" if upgrade else "fully upgraded")
            )
        elif tile in self.game.plots:
            print(f"  {label}: empty build plot")
        elif tile in self.path_tiles:
            print(f"  {label}: road")
        elif tile in self.decor:
            print(f"  {label}: {self.decor[tile]} (scenery)")
        else:
            print(f"  {label}: open ground — nothing can be built here")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def execute(self, line: str) -> bool:
        """Run one command. Returns ``False`` when the user wants to quit."""
        try:
            parts = shlex.split(line)
        except ValueError as exc:
            print(c("warn", f"  {exc}"))
            return True
        if not parts:
            return True
        command, *args = parts
        command = command.lower()

        try:
            if command in {"quit", "exit", "q"}:
                return False
            if command in {"help", "h", "?"}:
                print(HELP)
            elif command == "legend":
                print(LEGEND)
            elif command in {"map", "m"}:
                self.show()
            elif command in {"build", "b"}:
                self._cmd_build(args)
            elif command in {"upgrade", "u"}:
                self._cmd_upgrade(args)
            elif command in {"sell", "s"}:
                self._cmd_sell(args)
            elif command in {"target", "t"}:
                self._cmd_target(args)
            elif command in {"wave", "w"}:
                wave = self.game.start_wave()
                print(
                    c(
                        "info",
                        f"  Wave {self.game.wave_number} incoming: {wave.summary()}",
                    )
                )
                self.game.drain_events()
                self.show()
            elif command in {"step", ".", "tick"}:
                self._cmd_step(args)
            elif command in {"run", "r"}:
                self._cmd_run(args)
            elif command == "towers":
                self.list_towers()
            elif command == "shop":
                self.list_shop()
            elif command == "waves":
                self.list_waves()
            elif command in {"info", "i"}:
                if not args:
                    print(c("warn", "  usage: info <tile>"))
                else:
                    self.describe_tile(parse_tile(args[0]))
            else:
                print(c("warn", f"  unknown command {command!r} — try 'help'"))
        except BuildError as exc:
            print(c("warn", f"  {exc}"))
        except ValueError as exc:
            print(c("warn", f"  {exc}"))
        return True

    def _cmd_build(self, args: list[str]) -> None:
        if len(args) < 2:
            print(c("warn", "  usage: build <tile> <tower>   (see 'shop')"))
            return
        tile = parse_tile(args[0])
        tower = self.game.build(tile, args[1].lower())
        print(
            c(
                "good",
                f"  Built {tower.kind.name} at {tile_label(tile)} "
                f"for {tower.kind.cost}g — {self.game.gold}g left",
            )
        )
        self.game.drain_events()

    def _cmd_upgrade(self, args: list[str]) -> None:
        if not args:
            print(c("warn", "  usage: upgrade <tile>"))
            return
        tile = parse_tile(args[0])
        tower = self.game.upgrade(tile)
        print(
            c(
                "good",
                f"  {tile_label(tile)} is now {tower.label} — {self.game.gold}g left",
            )
        )
        self.game.drain_events()

    def _cmd_sell(self, args: list[str]) -> None:
        if not args:
            print(c("warn", "  usage: sell <tile>"))
            return
        tile = parse_tile(args[0])
        refund = self.game.sell(tile)
        print(c("good", f"  Sold the tower at {tile_label(tile)} for {refund}g"))
        self.game.drain_events()

    def _cmd_target(self, args: list[str]) -> None:
        if len(args) < 2:
            modes = ", ".join(m.value for m in TargetMode)
            print(c("warn", f"  usage: target <tile> <{modes}>"))
            return
        tile = parse_tile(args[0])
        try:
            tower = self.game.set_target_mode(tile, args[1].lower())
        except ValueError:
            modes = ", ".join(m.value for m in TargetMode)
            print(c("warn", f"  target mode must be one of: {modes}"))
            return
        print(c("good", f"  {tile_label(tile)} now targets {tower.target_mode.value}"))

    def _cmd_step(self, args: list[str]) -> None:
        seconds = float(args[0]) if args else 1.0
        seconds = max(0.0, min(seconds, 120.0))
        self.game.run_seconds(seconds)
        self.report_events()
        self.show()

    def _cmd_run(self, args: list[str]) -> None:
        """Advance until the current wave ends, the run ends, or the cap hits."""
        limit = float(args[0]) if args else 120.0
        limit = max(0.0, min(limit, 600.0))
        target_wave = self.game.wave_index
        elapsed = 0.0
        while elapsed < limit and not self.game.is_over:
            self.game.step()
            elapsed += 1 / 60
            if self.game.wave_index > target_wave:
                break
        self.report_events()
        self.show()


def choose_level(paths: list[Path], index: int | None) -> Level:
    """Load a level by 1-based index, defaulting to the first."""
    if not paths:
        raise SystemExit("No level files found in levels/.")
    position = 0 if index is None else index - 1
    if not 0 <= position < len(paths):
        raise SystemExit(f"Level {index} does not exist (1-{len(paths)} available).")
    return Level.load(paths[position])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tick-based terminal tower defense",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--level", type=int, default=None, help="level number to play")
    parser.add_argument(
        "--list-levels", action="store_true", help="print the level list and exit"
    )
    parser.add_argument(
        "--script",
        default=None,
        help="read commands from a file instead of the keyboard",
    )
    parser.add_argument("--seed", type=int, default=None, help="seed the engine's RNG")
    parser.add_argument(
        "--no-color", action="store_true", help="disable ANSI colour output"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.no_color or not sys.stdout.isatty():
        disable_colour()
    paths = discover_levels()
    if args.list_levels:
        for index, path in enumerate(paths, start=1):
            level = Level.load(path)
            print(
                f"{index}. {level.name} — {level.cols}x{level.rows}, "
                f"{len(level.waves)} waves, {len(level.plots)} plots"
            )
            if level.description:
                print(f"   {level.description}")
        return 0

    level = choose_level(paths, args.level)
    session = TerminalGame(level, seed=args.seed)
    print(c("bold", f"\n=== Tower Defense — {level.name} ==="))
    if level.description:
        print(c("dim", level.description))
    print(c("dim", "Type 'help' for commands, 'legend' for the map key.\n"))
    session.show()
    print(
        c("info", "\nTip: build a couple of gun turrets, then 'run' to fight the wave.")
    )

    lines: list[str] = []
    if args.script:
        lines = Path(args.script).read_text(encoding="utf-8").splitlines()

    while True:
        if lines:
            line = lines.pop(0)
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            print(c("dim", f"> {line}"))
        else:
            if args.script:
                break
            try:
                line = input(c("bold", "> "))
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if not session.execute(line):
            break
        if session.game.is_over and not lines:
            print(c("bold", "\nFinal stats:"))
            for key, value in session.game.stats().items():
                print(f"  {key}: {value}")
            break
    print("Goodbye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
