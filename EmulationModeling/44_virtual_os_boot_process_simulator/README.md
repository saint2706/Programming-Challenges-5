# Virtual OS Boot Process Simulator

Simulates the boot sequence of an operating system as a Dependency Graph (DAG).

## How to Run

```bash
python EmulationModeling/44_virtual_os_boot_process_simulator/main.py
```

## Logic

1.  **Stages**: Nodes in the graph (BIOS, Kernel, Services).
2.  **Dependencies**: Edges. A stage cannot start until all its dependencies are DONE.
3.  **SimPy Events**: Used to coordinate the DAG execution (`yield simpy.all_of(...)`).
4.  **Visualization**: Shows the DAG nodes changing color from Gray (Pending) to Orange (Running) to Green (Done).
