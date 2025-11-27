# Weather Pattern Cellular Model

This module simulates a toy atmospheric system on a 2D grid. Each cell tracks
pressure, humidity, and a wind vector. During each tick:

- **Pressure diffusion** spreads pressure using a 4-neighbor Laplacian.
- **Wind-driven moisture transport** advects humidity along the wind field while
  clamping values to the `[0, 1]` range.

The default parameters initialize realistic variations around sea-level
pressure with mild random humidity and wind.

## Running the demo

The repository includes a small CLI that runs the simulation and renders a
matplotlib heatmap of the final pressure field.

```bash
python EmulationModeling/16_weather_pattern_cellular_model/demo.py --steps 80 --width 80 --height 80 --output pressure.png
```

This uses a headless backend and writes a PNG image instead of opening a
window. Example defaults:

- `--diffusion-rate 0.15`
- `--moisture-transport-rate 0.1`
- `--dt 1.0`
- `--seed 7`

## Using the model programmatically

```python
from EmulationModeling.16_weather_pattern_cellular_model.weather_model import WeatherGrid

grid = WeatherGrid(width=64, height=64, diffusion_rate=0.2, moisture_transport_rate=0.08, dt=0.5, seed=1)
for _ in range(100):
    grid.step()
pressure_snapshot = grid.snapshot()
cell = grid.cell_at(10, 10)
```

- `pressure_snapshot` is a NumPy array containing the latest pressure values.
- `cell` gives the pressure, humidity, and wind vector for a single grid cell.
