"""Search algorithm demonstrations on a sample grid.

This module implements Breadth-First Search (BFS), Depth-First Search (DFS),
and A* search using Manhattan distance on a simple grid. The test harness
constructs an example grid with obstacles, runs each algorithm from a start
position to a goal, and prints the resulting paths and annotated grids.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Coordinate = Tuple[int, int]


@dataclass
class SearchResult:
    """Container for a path result."""

    path: Optional[List[Coordinate]]
    visited: Set[Coordinate]


def manhattan(a: Coordinate, b: Coordinate) -> int:
    """Return the Manhattan distance between two coordinates."""

    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(grid: Grid, node: Coordinate) -> Iterable[Coordinate]:
    """Generate traversable neighbor coordinates (4-connected)."""

    row, col = node
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in deltas:
        nr, nc = row + dr, col + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == 0:
            yield nr, nc


def reconstruct_path(
    parents: Dict[Coordinate, Coordinate], goal: Coordinate
) -> List[Coordinate]:
    """Reconstruct a path from start to goal using the parent map."""

    path: List[Coordinate] = [goal]
    while path[-1] in parents:
        path.append(parents[path[-1]])
    path.reverse()
    return path


def bfs(grid: Grid, start: Coordinate, goal: Coordinate) -> SearchResult:
    """Perform Breadth-First Search from start to goal."""

    queue: deque[Coordinate] = deque([start])
    parents: Dict[Coordinate, Coordinate] = {}
    visited: Set[Coordinate] = {start}

    while queue:
        current = queue.popleft()
        if current == goal:
            return SearchResult(reconstruct_path(parents, goal), visited)

        for neighbor in neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                parents[neighbor] = current
                queue.append(neighbor)

    return SearchResult(None, visited)


def dfs(grid: Grid, start: Coordinate, goal: Coordinate) -> SearchResult:
    """Perform Depth-First Search from start to goal."""

    stack: List[Coordinate] = [start]
    parents: Dict[Coordinate, Coordinate] = {}
    visited: Set[Coordinate] = set()

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            return SearchResult(reconstruct_path(parents, goal), visited)

        for neighbor in neighbors(grid, current):
            if neighbor not in visited:
                parents.setdefault(neighbor, current)
                stack.append(neighbor)

    return SearchResult(None, visited)


def a_star(
    grid: Grid,
    start: Coordinate,
    goal: Coordinate,
    heuristic: Callable[[Coordinate, Coordinate], int] = manhattan,
) -> SearchResult:
    """Perform A* search from start to goal using the provided heuristic."""

    open_set: List[Tuple[int, Coordinate]] = []
    heappush(open_set, (heuristic(start, goal), start))
    parents: Dict[Coordinate, Coordinate] = {}
    g_scores: Dict[Coordinate, int] = {start: 0}
    visited: Set[Coordinate] = set()

    while open_set:
        _, current = heappop(open_set)
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            return SearchResult(reconstruct_path(parents, goal), visited)

        current_cost = g_scores[current]
        for neighbor in neighbors(grid, current):
            tentative_g = current_cost + 1
            if tentative_g < g_scores.get(neighbor, float("inf")):
                parents[neighbor] = current
                g_scores[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heappush(open_set, (f_score, neighbor))

    return SearchResult(None, visited)


def format_grid_with_path(
    grid: Grid,
    path: Optional[Sequence[Coordinate]],
    start: Coordinate,
    goal: Coordinate,
) -> str:
    """Return a string visualizing the grid with the path overlaid."""

    visual = []
    path_set = set(path) if path else set()

    for r, row in enumerate(grid):
        cells = []
        for c, cell in enumerate(row):
            coord = (r, c)
            if coord == start:
                cells.append("S")
            elif coord == goal:
                cells.append("G")
            elif cell == 1:
                cells.append("#")
            elif coord in path_set:
                cells.append("*")
            else:
                cells.append(".")
        visual.append(" ".join(cells))
    return "\n".join(visual)


def run_demo() -> None:
    """Run BFS, DFS, and A* on a sample grid and print the results."""

    grid: Grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    start = (0, 0)
    goal = (5, 5)

    algorithms = {
        "Breadth-First Search": bfs,
        "Depth-First Search": dfs,
        "A* Search": a_star,
    }

    for name, algorithm in algorithms.items():
        result = algorithm(grid, start, goal)
        print(f"\n{name}:")
        if result.path:
            print(f"Path length: {len(result.path)}")
            print("Path:", result.path)
            print(format_grid_with_path(grid, result.path, start, goal))
        else:
            print("No path found.")


if __name__ == "__main__":
    run_demo()
