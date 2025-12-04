# 3D Rigid Body Physics Engine

A simple physics engine simulating rigid bodies falling and colliding with the floor.

## How to Run

```bash
python EmulationModeling/49_3d_rigid_body_physics_engine/main.py
```

## Logic

1.  **RigidBody**: State includes position, velocity, and mass.
2.  **PhysicsWorld**: Manages bodies and gravity.
3.  **Integration**: Symplectic Euler method used in `simulation_core/physics.py`.
4.  **Collisions**: Simple floor collision response (bounce with restitution).
5.  **Visualization**: 3D scatter plot using `matplotlib`.
