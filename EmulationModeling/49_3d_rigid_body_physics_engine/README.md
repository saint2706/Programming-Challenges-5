# 3D Rigid Body Physics Engine

A simple physics engine simulating rigid bodies falling and colliding with the floor.

## 📋 Table of Contents

- [Theory](#theory)
- [How to Run](#how-to-run)

## 🧠 Theory

### Core Components

1. **RigidBody**: position, velocity, mass, and radius.
2. **PhysicsWorld**: applies gravity and steps all bodies.
3. **Integration**: Symplectic Euler updates velocity then position.
4. **Collisions**: Floor collision reverses vertical velocity with restitution.

### Ideal Example Test Case (Exercises Edge Cases)

**Setup:**
- Two bodies, radius 0.5
- Gravity = (0, -9.81, 0)
- Body A at y=1.0 with velocity (0, -1, 0) (already moving down)
- Body B at y=0.4 with velocity (0, 0, 0) (intersects the floor)
- Restitution = 0.5

This case covers:
- **Regular fall** (A continues downward until impact).
- **Immediate collision** (B starts below floor threshold).
- **Velocity reversal** and energy loss due to restitution.

### Step-by-Step Walkthrough

1. **Apply gravity**
   - Each body’s velocity decreases by `g * dt` in the y-direction.

2. **Integrate positions**
   - Positions update using the new velocities (symplectic Euler).

3. **Collision check**
   - If `position.y - radius < 0`, the body intersects the floor.

4. **Resolve collision**
   - Clamp the body to `y = radius`.
   - Invert and scale vertical velocity: `vy = -vy * restitution`.

5. **Outcome**
   - Body A eventually hits the floor and bounces with reduced speed.
   - Body B is corrected immediately and gains upward velocity due to restitution.

This example demonstrates both normal integration and edge-case collision correction.

## ▶️ How to Run

```bash
python EmulationModeling/49_3d_rigid_body_physics_engine/main.py
```
