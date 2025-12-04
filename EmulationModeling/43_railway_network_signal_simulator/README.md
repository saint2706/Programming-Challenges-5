# Railway Network Signal Simulator

Simulates a railway track with block signaling to prevent collisions.

## How to Run

```bash
python EmulationModeling/43_railway_network_signal_simulator/main.py
```

## Logic

1.  **Blocks**: The track is divided into segments. Only one train can occupy a block at a time.
2.  **Signals**: Protect entry to blocks. If a block is occupied, the signal is red (SimPy resource locked).
3.  **Trains**: Request access to the next block before entering. If denied, they wait (stop).
4.  **Visualization**: Shows trains moving along a linear track, with blocks turning red when occupied.
