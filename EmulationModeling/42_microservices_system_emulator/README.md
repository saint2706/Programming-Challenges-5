# Microservices System Emulator

Simulates a graph of microservices with cold starts, latency, and failure propagation.

## How to Run

```bash
python EmulationModeling/42_microservices_system_emulator/main.py
```

## Logic

1.  **Services**: Defined as nodes in a DAG (e.g., Gateway -> Product -> DB).
2.  **Requests**: Enter the system at the Gateway and propagate to dependencies.
3.  **Failures**: Random failures occur and propagate up the stack.
4.  **Queues**: SimPy Resources limit concurrency, simulating bottlenecks.
5.  **Visualization**: Shows the service graph with request counts and failure stats over time.
