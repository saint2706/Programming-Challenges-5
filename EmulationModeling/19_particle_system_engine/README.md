# Particle System Engine

A lightweight Python particle engine that supports both Python list-based updates
and NumPy-vectorized updates. Particles store position, velocity, and remaining
lifetime and can optionally be influenced by gravity.

## Features

- Simple `Particle` dataclass for clear state management.
- `ParticleEngine.update` can use either list-based or vectorized update paths.
- Helper to initialize random particles for quick experiments.
- Matplotlib sample animation (run the module directly) that visualizes the
  vectorized update path with fading particles.

## Usage

```bash
python EmulationModeling/16_particle_system_engine/particle_engine.py
```

To integrate into other scripts (directory name starts with a digit, so use
`importlib`):

```python
import importlib
import numpy as np

pe = importlib.import_module("EmulationModeling.16_particle_system_engine.particle_engine")
engine = pe.ParticleEngine(gravity=np.array([0.0, -9.81]))
engine.add_particles(positions=[(0, 0)], velocities=[(2, 4)], lifetimes=[5.0])
engine.update(dt=0.016, use_vectorized=False)  # or True for NumPy path
print(engine.positions())
```
