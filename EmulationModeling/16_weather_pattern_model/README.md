# Weather Pattern Cellular Model

This module simulates a toy atmospheric system on a 2D grid. Each cell tracks pressure, humidity, and a wind vector.

## 📋 Table of Contents

- [Theory](#theory)
- [Running the Demo](#running-the-demo)
- [Programmatic Usage](#programmatic-usage)

## 🧠 Theory

### Model Components

Each grid cell contains:
- **Pressure** (scalar)
- **Humidity** (scalar in [0, 1])
- **Wind** (2D vector)

Each simulation step performs:
1. **Pressure diffusion** using a 4-neighbor Laplacian (smooths extremes).
2. **Moisture transport** by advecting humidity along the wind field.
3. **Clamping** to keep humidity within physical bounds.

### Ideal Example Test Case (Exercises Edge Cases)

**Setup:**
- Grid: 3 × 3
- Pressure initialized with a single high-pressure center.
- Humidity initialized with a single saturated corner.
- Wind vectors set to push moisture diagonally.

Initial pressure (P):
```
[ [1000, 1000, 1000],
  [1000, 1020, 1000],
  [1000, 1000, 1000] ]
```

Initial humidity (H):
```
[ [1.0, 0.0, 0.0],
  [0.0, 0.0, 0.0],
  [0.0, 0.0, 0.0] ]
```

Wind (W):
- All cells: (1, 1) (pushes toward bottom-right)

### Step-by-Step Walkthrough

1. **Pressure diffusion**
   - The center cell (1020) is higher than neighbors (1000).
   - The Laplacian spreads pressure outward, slightly lowering the center and raising adjacent cells.

2. **Moisture advection**
   - Humidity from the top-left corner is pushed diagonally toward the center.
   - Values remain in [0, 1] due to clamping, preventing oversaturation.

3. **Boundary handling**
   - The corner cell cannot draw moisture from outside the grid, so its transport only uses valid neighbors.

4. **Result after one step**
   - Pressure becomes smoother.
   - Humidity is redistributed without exceeding bounds.

This example tests diffusion from a spike, advection along wind, and boundary clamping.

## 🚀 Running the Demo

```bash
python EmulationModeling/16_weather_pattern_model/demo.py --steps 80 --width 80 --height 80 --summary pressure_summary.txt
```

Example defaults:
- `--diffusion-rate 0.15`
- `--moisture-transport-rate 0.1`
- `--dt 1.0`
- `--seed 7`

## 🧪 Programmatic Usage

```python
from EmulationModeling.16_weather_pattern_model.weather_model import WeatherGrid

grid = WeatherGrid(width=64, height=64, diffusion_rate=0.2, moisture_transport_rate=0.08, dt=0.5, seed=1)
for _ in range(100):
    grid.step()
pressure_snapshot = grid.snapshot()
cell = grid.cell_at(10, 10)
```

- `pressure_snapshot` is a NumPy array containing the latest pressure values.
- `cell` gives the pressure, humidity, and wind vector for a single grid cell.
