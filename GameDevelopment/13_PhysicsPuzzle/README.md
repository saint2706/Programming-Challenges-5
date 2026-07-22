# Physics Puzzle Game

A slingshot physics puzzle powered by a small, dependency-free 2D physics
engine. Launch the blue ball to knock the orange target into the green goal —
arcing over walls and dodging pits along the way. Every level is authored as a
JSON file, so new puzzles need no code changes.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)
- [Level Format](#level-format)
- [Testing](#testing)

## ✨ Features

- **Custom 2D physics engine** (`physics.py`): gravity, circular bodies,
  restitution (bounciness), friction, and collision resolution for
  circle-vs-wall and circle-vs-circle contacts.
- **Fixed-timestep, sub-stepped integrator** for deterministic, stable
  simulation (and reproducible tests).
- **Slingshot aiming** with a live trajectory preview.
- **Data-driven levels** (`levels/*.json`): walls, obstacles, a goal region and
  optional hazard pits — load, retry and cycle between them at runtime.
- **Win/lose logic** decoupled from rendering, so the whole puzzle can be
  simulated headlessly.
- **Pygame renderer** (`main.py`) with goal/hazard highlighting and status
  banners.

## 🏗️ Architecture

```
physics.py   Pure-Python 2D physics (no dependencies)
 ├─ Vec2      2D vector maths
 ├─ Rect      Axis-aligned rectangle (walls, goal, hazards)
 ├─ Body      Dynamic circle (position, velocity, mass, restitution, friction)
 └─ World     Integrator + collision resolution + world bounds

levels.py    Level data + puzzle rules (no rendering)
 ├─ Level      Parsed level (from JSON dict / file)
 ├─ PuzzleGame World wrapper: launch, update, win/lose detection, reset
 └─ discover_levels()  Finds level JSON files

main.py      Pygame front-end (rendering, input, trajectory preview)
levels/      JSON level definitions
```

`physics.py` and `levels.py` contain no `pygame` imports, which is what lets the
engine and puzzle logic be unit-tested without a display.

## 💻 Installation

The engine, levels and tests are pure standard-library Python (3.10+). The
graphical front-end additionally needs Pygame:

```bash
pip install pygame
cd GameDevelopment/13_PhysicsPuzzle
```

## 🚀 Usage

```bash
python main.py
```

## 🎮 Controls

| Action        | Control                                             |
| :------------ | :-------------------------------------------------- |
| **Aim/Launch** | Click and drag on the blue ball, release to fire    |
| **Retry**     | R                                                   |
| **Next level** | N                                                   |
| **Prev level** | P                                                   |
| **Quit**      | ESC                                                 |

Pull back from the ball slingshot-style; a dotted yellow line previews the arc.

## 🧩 Level Format

Levels are JSON. Coordinates use screen conventions (``y`` increases downward).

```json
{
  "name": "Warmup Roll",
  "description": "Roll the target into the goal.",
  "width": 800,
  "height": 600,
  "gravity": [0, 900],
  "max_power": 1400,
  "launch": { "x": 120, "y": 523, "radius": 15, "restitution": 0.4 },
  "target": { "x": 400, "y": 522, "radius": 18, "friction": 0.02 },
  "goal":   { "x": 620, "y": 460, "w": 170, "h": 100 },
  "walls":  [ { "x": 0, "y": 560, "w": 800, "h": 40, "name": "floor" } ],
  "obstacles": [ { "x": 300, "y": 400, "radius": 20, "mass": 1.5 } ],
  "hazards": [ { "x": 340, "y": 470, "w": 180, "h": 130, "name": "pit" } ]
}
```

- **launch / target / obstacles** — circular balls (`radius`, optional `mass`,
  `restitution`, `friction`). The target must reach the goal.
- **goal** — rectangle the target must enter to win.
- **walls** — solid rectangles the balls collide with.
- **hazards** — rectangles that cause a loss if the target enters them.
- **max_power** — caps the launch speed.

Three levels ship in `levels/`: a warm-up roll, an arc-over-a-wall puzzle, and a
pit to clear.

## 🧪 Testing

The physics engine and puzzle logic are covered by a headless test suite
(no Pygame required):

```bash
python test_game.py        # standalone runner with tick-marks
# or
python -m pytest test_game.py
```
