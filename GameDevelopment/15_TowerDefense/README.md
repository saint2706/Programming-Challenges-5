# Tower Defense Game

Enemies follow a waypoint path; towers sit on plots beside it and shoot whatever
comes into range. Five tower types with three upgrade tiers each, five enemy
archetypes including armoured and airborne, and data-driven waves — plus a
Pygame front-end **and** a tick-based terminal front-end over one shared engine.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)
- [Towers and Enemies](#towers-and-enemies)
- [Level Format](#level-format)
- [Assets](#assets)
- [Testing](#testing)

## ✨ Features

- **Fixed-timestep deterministic engine.** `core.py` advances in 1/60 s ticks, so
  the same level plus the same build orders always produces the same result —
  which is what makes the combat maths testable and the terminal version honest.
- **Five towers, three tiers each.** Gun, Gatling, Frost (slows), Mortar (splash,
  ground only, pierces armour) and Flak Battery (anti-air only). Each tier costs
  gold and raises damage, fire rate and range.
- **Five enemy archetypes.** Grunts, fast Runners, Armoured Cars that shrug off
  small-calibre fire, Bombers that ignore the road and fly straight to the exit,
  and a Juggernaut wave boss that costs six lives if it leaks.
- **Real counterplay.** Flat armour subtracts from every hit (a hit always lands
  for at least 1), armour piercing bypasses it, slows stack by taking whichever
  effect is harsher, and splash hits everything inside its radius.
- **Per-tower targeting.** First along the path (default), last, closest, or
  strongest — switchable in play.
- **Data-driven waves.** Waves are groups of `(enemy, count, interval, delay,
hp_scale)` in JSON, with a clear bonus per wave. Three levels ship: 8, 10 and
  12 waves.
- **Economy that matters.** Bounties, wave rewards, upgrade costs and a 60 %
  refund on sales, with a build phase that auto-starts the next wave if you dawdle.
- **Two front-ends, one engine.** `main.py` draws real-time Pygame with CC0
  Kenney sprites, rotating turrets, health bars, explosion puffs, floating gold
  and a 1×/2×/4× speed control. `terminal.py` renders the same state as ASCII and
  advances the clock only when you say so.

## 🏗️ Architecture

```
core.py        The whole simulation — no pygame import anywhere
 ├─ Vec2        Immutable 2D vector (angle_degrees drives sprite rotation)
 ├─ Route       Waypoint polyline with distance-based position/heading lookup
 ├─ TowerKind   Archetype + TowerTier upgrade ladder     (TOWER_KINDS catalogue)
 ├─ EnemyKind   HP, speed, armour, bounty, flying flag   (ENEMY_KINDS catalogue)
 ├─ Level       Geometry, build plots, economy, waves; validates its own JSON
 ├─ Enemy       Path progress, slow effects, armour-aware damage
 ├─ Tower       Tier stats, cooldown, targeting, kill/damage tracking
 ├─ Projectile  Homing shot; resolves splash and slow on impact
 └─ TowerDefenseGame  step(dt), build/upgrade/sell, waves, gold, lives, events

levels/*.json  Three hand-authored levels
main.py        Pygame renderer: map, sprites, sidebar shop, effects, sound
terminal.py    Tick-based ASCII front-end with a command shell
fetch_assets.py  Downloads the CC0 Kenney packs and slices the tilesheet
assets/        Committed sprites, fonts, sound (+ CREDITS.md)
```

58 headless tests (no pygame, no display) live in
`tests/GameDevelopment/test_15_tower_defense.py`.

The engine exposes a small event queue (`shoot`, `hit`, `kill`, `leak`, `build`,
`wave`, `end`) that the renderer turns into sounds and particles. The engine
itself never knows either exists.

## 💻 Installation

The engine, the levels, the terminal front-end and the tests are pure
standard-library Python (3.10+). The graphical front-end needs Pygame:

```bash
pip install pygame
cd GameDevelopment/15_TowerDefense
```

The sprites, fonts and sounds are committed, so nothing needs downloading. To
refresh them from source (which needs `Pillow` to slice the tilesheet):

```bash
python fetch_assets.py --force
```

## 🚀 Usage

### Graphical version

```bash
python main.py                 # Training Ground
python main.py --level 3       # Airfield Assault
python main.py --list-levels
```

### Terminal version

Time only moves when you tell it to, so you can think between orders:

```bash
python terminal.py                    # Training Ground
python terminal.py --level 2
python terminal.py --list-levels
python terminal.py --script orders.txt   # replay a file of commands
```

```
    a b c d e f g h i j k l m n o p
  1 ................................
  2 ..^^........[]..[]......^^......
  3 ..........::::::::::::..........
  4 ........[]::A1[][]..::....nn....
  5 ....[]G1..::......[]::..,,......
  6 >>::::::::::........::......^^..
  7 ....[]G1......[]..[]::..........
  8 ..............[]....::[][][]....
  9 ..nn................::::::::::<<
 10 ....^^..,,............[]..[]....
 11 ................................
gold 299 | lives 20 | wave 4/8 | t   55.5s | score 289
BUILDING — auto-start in 10.0s — next: 12x Runner
```

A typical opening:

```
build d5 gun
build d7 gun
build g4 gatling
wave          # send it now instead of waiting out the build phase
run           # fast-forward until the wave is over
towers        # see what each turret killed
```

## 🎮 Controls

### Graphical version

| Action                    | Control                                                     |
| :------------------------ | :---------------------------------------------------------- |
| **Build**                 | Pick a tower (click its card or `1`–`5`), then click a plot |
| **Inspect / select**      | Left click a built tower — shows its range ring             |
| **Upgrade / sell**        | `U` / `S`, or the sidebar buttons                           |
| **Cycle targeting**       | `T`, or the sidebar button                                  |
| **Send next wave**        | `SPACE`, or the sidebar button                              |
| **Pause**                 | `P`                                                         |
| **Game speed (1×/2×/4×)** | `F`                                                         |
| **Restart level**         | `R`                                                         |
| **Next / previous level** | `N` / `B`                                                   |
| **Controls overlay**      | `F1`                                                        |
| **Deselect, then quit**   | `ESC` (right click also deselects)                          |

Hovering a plot with a tower selected previews its range in green, or red when
the plot is taken or you cannot afford it.

### Terminal version

| Command                     | Short | Effect                                        |
| :-------------------------- | :---- | :-------------------------------------------- |
| `build <tile> <tower>`      | `b`   | Place a tower, e.g. `b c5 gun`                |
| `upgrade <tile>`            | `u`   | Advance one tier                              |
| `sell <tile>`               | `s`   | Remove for a 60 % refund                      |
| `target <tile> <mode>`      | `t`   | `first`, `last`, `closest`, `strongest`       |
| `wave`                      | `w`   | Send the next wave immediately                |
| `step [seconds]`            | `.`   | Advance the clock (default 1 s)               |
| `run [seconds]`             | `r`   | Advance until the wave ends (cap 120 s)       |
| `map`                       | `m`   | Redraw                                        |
| `towers` / `shop` / `waves` |       | List your towers, the catalogue, the schedule |
| `info <tile>`               | `i`   | Describe one tile                             |
| `legend` / `help`           |       | Map key / command list                        |

Tiles are named like a chessboard: `c5` is column c, row 5. `2,4` also works.

## 🏰 Towers and Enemies

| Tower            | Cost | Damage |   Rate | Range | Notes                                           |
| :--------------- | ---: | -----: | -----: | ----: | :---------------------------------------------- |
| **Gun Turret**   |   60 |      9 |  1.6/s |   120 | Cheap all-rounder                               |
| **Gatling**      |  110 |      5 |  6.0/s |   105 | Shreds swarms; armour blunts it badly           |
| **Frost Tower**  |   90 |      4 |  1.2/s |   115 | Slows to 55 % speed for 2 s                     |
| **Mortar**       |  150 |     26 | 0.55/s |   185 | 52 px splash, pierces 3 armour, **ground only** |
| **Flak Battery** |  120 |     14 |  2.2/s |   160 | 26 px splash, **air only**                      |

| Enemy            |  HP | Speed | Armour | Bounty | Leak | Notes                        |
| :--------------- | --: | ----: | -----: | -----: | ---: | :--------------------------- |
| **Grunt**        |  45 |    52 |      0 |      8 |    1 | The baseline                 |
| **Runner**       |  28 |   104 |      0 |      9 |    1 | Twice the speed, half the HP |
| **Armoured Car** |  95 |    44 |      4 |     16 |    1 | Ignores light weapons        |
| **Bomber**       |  70 |    88 |      0 |     20 |    1 | Flies the straight air lane  |
| **Juggernaut**   | 620 |    30 |      9 |    110 |    6 | Wave boss                    |

Because armour is subtracted per hit, the Gatling's 5-damage burst does only 1
per shot to an Armoured Car while the Mortar's 26 does 25 — matching the right
tower to the right target is the whole game. Levels 2 and 3 also scale enemy HP
per wave via `hp_scale`.

## 🧩 Level Format

Levels are JSON in `levels/`. Coordinates are **tile** coordinates, and
consecutive waypoints must share a row or a column so the road can be drawn as
whole tiles (the loader raises on a diagonal pair). `Level.__post_init__` also
rejects build plots that sit on the road or off the map, so a broken level fails
at load rather than mid-game.

```json
{
  "name": "Training Ground",
  "description": "A gentle S-bend to learn the ropes.",
  "cols": 16,
  "rows": 11,
  "tile_size": 48,
  "starting_gold": 240,
  "starting_lives": 20,
  "wave_break": 10.0,
  "waypoints": [
    [0, 5],
    [5, 5],
    [5, 2],
    [10, 2],
    [10, 8],
    [15, 8]
  ],
  "plots": [
    [2, 4],
    [3, 4],
    [6, 3]
  ],
  "decor": [
    [1, 1, "tree"],
    [13, 3, "rock"]
  ],
  "waves": [
    {
      "name": "Outriders",
      "reward": 32,
      "groups": [
        { "enemy": "grunt", "count": 6, "interval": 1.0 },
        {
          "enemy": "runner",
          "count": 4,
          "interval": 0.7,
          "delay": 4.0,
          "hp_scale": 1.2
        }
      ]
    }
  ]
}
```

- **waypoints** — the ground path, entry first, exit last. Aircraft ignore it and
  fly straight from the entry tile to the exit tile.
- **plots** — the only tiles a tower may occupy.
- **decor** — cosmetic props (`tree`, `bush`, `rock`).
- **waves[].groups** — `enemy`, `count`, `interval` between spawns, `delay` after
  the wave starts, and `hp_scale` to toughen late waves.

The three shipped levels are a gentle S-bend (8 waves), a long switchback
(10 waves) and an air-heavy map where the straight flight lane cuts across the
ground route (12 waves).

## 🎨 Assets

All art, fonts and sound are **CC0** (public domain) by
[Kenney](https://kenney.nl/assets). Sprites are individual 64 px tiles sliced out
of the _Tower Defense (top-down)_ tilesheet by `fetch_assets.py`, which resolves
each pack's current download URL, caches the ZIP under `.asset-cache/`
(git-ignored) and writes only the 22 tiles the game draws. Fonts come from Kenney
Fonts, sound from Sci-Fi Sounds, UI Audio and Interface Sounds. See
[assets/CREDITS.md](assets/CREDITS.md) for the tile-by-tile mapping.

The pack has no blue turret, so the Frost Tower reuses a grey head and the
renderer tints it icy blue. If `assets/` is missing entirely the game still runs,
drawing vector placeholders and warning in the sidebar.

## 🧪 Testing

58 headless tests cover geometry, level validation, the build economy,
targeting, damage/armour/slow/splash, wave scheduling and the win/lose
conditions — no display required:

```bash
python tests/GameDevelopment/test_15_tower_defense.py  # standalone runner with tick-marks
# or
python -m pytest tests/GameDevelopment/test_15_tower_defense.py
```

Because the engine is deterministic, one of the tests simply plays the same
opening twice and asserts the resulting statistics are byte-identical.
