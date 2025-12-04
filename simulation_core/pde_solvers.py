import numpy as np
import numba

@numba.jit(nopython=True)
def diffusion_step_2d(grid: np.ndarray, diff: float, dt: float, dx: float, dy: float) -> np.ndarray:
    """
    Simple 2D diffusion using finite difference.
    dC/dt = D * (d^2C/dx^2 + d^2C/dy^2)
    """
    ny, nx = grid.shape
    new_grid = grid.copy()

    alpha_x = diff * dt / (dx * dx)
    alpha_y = diff * dt / (dy * dy)

    for i in range(1, ny - 1):
        for j in range(1, nx - 1):
            new_grid[i, j] = grid[i, j] + \
                             alpha_x * (grid[i, j+1] - 2*grid[i, j] + grid[i, j-1]) + \
                             alpha_y * (grid[i+1, j] - 2*grid[i, j] + grid[i-1, j])
    return new_grid

@numba.jit(nopython=True)
def advect_step_2d(grid: np.ndarray, u: np.ndarray, v: np.ndarray, dt: float, dx: float, dy: float) -> np.ndarray:
    """
    Simple semi-Lagrangian advection or upwind scheme could go here.
    For simplicity, implementing a basic first-order upwind scheme.
    """
    ny, nx = grid.shape
    new_grid = grid.copy()

    for i in range(1, ny - 1):
        for j in range(1, nx - 1):
            # Upwind scheme
            # du/dx ~ (u[i,j] - u[i, j-1])/dx if u > 0

            grad_x = (grid[i, j] - grid[i, j-1])/dx if u[i,j] > 0 else (grid[i, j+1] - grid[i, j])/dx
            grad_y = (grid[i, j] - grid[i-1, j])/dy if v[i,j] > 0 else (grid[i+1, j] - grid[i, j])/dy

            new_grid[i, j] = grid[i, j] - dt * (u[i, j] * grad_x + v[i, j] * grad_y)

    return new_grid
