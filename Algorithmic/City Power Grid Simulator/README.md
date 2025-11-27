# City Power Grid Simulator

This challenge implements a simplified electrical grid simulator. The grid is modeled as a graph with generators, consumers, and transmission lines. Power is routed along available paths; overloaded lines fail and trigger re-routing, demonstrating cascading outages and load shedding.

## How it works
- **Nodes** can be generators (positive supply) or consumers (demand).
- **Edges** are transmission lines with a capacity limit and on/off status.
- A simulation step finds paths between generators with surplus and consumers with deficits, routing power along the shortest available path. The algorithm ignores capacity during routing to expose overloaded lines afterward.
- After each routing pass, any line that exceeded its capacity is marked failed and removed from the network; flows are recomputed until no overloads remain. Consumers that cannot be connected to any generator are shed.

## Running the demo
```bash
python grid_simulator.py
```
The demo scenario creates two generators, five consumers, and a handful of lines. It runs a healthy state, then triggers the failure of a major tie line. The simulation shows which lines overload and fail in response and how much consumer demand is shed.
