# Logistics & Routing Simulator

A SimPy + NetworkX based simulation of a logistics network. Trucks start at depots and deliver to customers with random demands.

## How to Run

```bash
python EmulationModeling/40_logistics_routing_simulator/main.py
```

## Logic

1.  **Depots**: Starting points for trucks.
2.  **Customers**: Have a demand and location.
3.  **Trucks**: Travel between nodes to satisfy demand. Simple greedy heuristic: find nearest feasible customer.
4.  **Visualization**: Generates `simulation.gif` in `output/` showing the fleet movement and delivery status.
