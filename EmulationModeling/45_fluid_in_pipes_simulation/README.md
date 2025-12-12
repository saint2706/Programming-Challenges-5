# Fluid in Pipes Simulation

Simulates fluid pressure and flow in a pipe network using ODEs.

## How to Run

```bash
python EmulationModeling/45_fluid_in_pipes_simulation/main.py
```

## Logic

1.  **Network**: Graph where nodes are junctions and edges are pipes with resistance.
2.  **Physics**:
    - Flow $Q_{uv} = (P_u - P_v) / R$ (Poiseuille-like).
    - Pressure change $\frac{dP}{dt} \propto \sum Q_{in} - \sum Q_{out}$ (Mass conservation with compressibility).
3.  **Boundary Conditions**: Node 0 is fixed High Pressure (Source), Node 3 is fixed Low Pressure (Sink).
4.  **Visualization**: Nodes colored by pressure (Red=High, Blue=Low), edge thickness represents flow rate.
