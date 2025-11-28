import math
import random
from typing import List, Tuple


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Label:
    def __init__(self, text: str, x: float, y: float, width: float, height: float):
        self.text = text
        self.target_x = x  # The point we want to label
        self.target_y = y
        self.width = width
        self.height = height

        # Current position (offset from target)
        # Positions: 0=TopRight, 1=TopLeft, 2=BottomRight, 3=BottomLeft
        self.position_idx = 0
        self.rect = self.get_rect()

    def get_rect(self) -> Tuple[float, float, float, float]:
        """Returns (x_min, y_min, x_max, y_max) based on current position."""
        # Padding
        p = 0.5

        if self.position_idx == 0:  # Top Right
            return (
                self.target_x + p,
                self.target_y + p,
                self.target_x + p + self.width,
                self.target_y + p + self.height,
            )
        elif self.position_idx == 1:  # Top Left
            return (
                self.target_x - p - self.width,
                self.target_y + p,
                self.target_x - p,
                self.target_y + p + self.height,
            )
        elif self.position_idx == 2:  # Bottom Right
            return (
                self.target_x + p,
                self.target_y - p - self.height,
                self.target_x + p + self.width,
                self.target_y - p,
            )
        elif self.position_idx == 3:  # Bottom Left
            return (
                self.target_x - p - self.width,
                self.target_y - p - self.height,
                self.target_x - p,
                self.target_y - p,
            )
        return (0, 0, 0, 0)

    def set_position(self, idx: int):
        self.position_idx = idx
        self.rect = self.get_rect()


def intersect(r1, r2) -> bool:
    """Check if two rectangles overlap."""
    # r = (min_x, min_y, max_x, max_y)
    return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])


class MapLabeler:
    """
    Uses Simulated Annealing to optimize label placement.
    Objective: Minimize overlaps and optimize preference (e.g. TopRight is best).
    """

    def __init__(self, labels: List[Label], bounds: Tuple[float, float, float, float]):
        self.labels = labels
        self.bounds = bounds  # (min_x, min_y, max_x, max_y) map bounds

    def energy(self) -> float:
        """
        Calculates total energy (cost).
        Energy = (Overlaps * Weight) + (OutOfBounds * Weight) + (PositionPreference)
        """
        overlap_weight = 1000
        boundary_weight = 500
        pref_weights = [
            0,
            2,
            5,
            10,
        ]  # TopRight(0) is best (cost 0), BottomLeft(3) is worst

        total_energy = 0

        # 1. Overlaps
        n = len(self.labels)
        for i in range(n):
            r1 = self.labels[i].rect

            # Position preference
            total_energy += pref_weights[self.labels[i].position_idx]

            # Boundary check
            if (
                r1[0] < self.bounds[0]
                or r1[2] > self.bounds[2]
                or r1[1] < self.bounds[1]
                or r1[3] > self.bounds[3]
            ):
                total_energy += boundary_weight

            for j in range(i + 1, n):
                r2 = self.labels[j].rect
                if intersect(r1, r2):
                    # Area of overlap could be used, but simple boolean count is faster
                    total_energy += overlap_weight

        return total_energy

    def solve(self, iterations: int = 10000, initial_temp: float = 100.0):
        current_energy = self.energy()
        temp = initial_temp

        for i in range(iterations):
            if temp <= 0:
                break

            # Pick random label
            idx = random.randint(0, len(self.labels) - 1)
            label = self.labels[idx]
            original_pos = label.position_idx

            # Pick random new position
            new_pos = random.randint(0, 3)
            if new_pos == original_pos:
                continue

            # Apply change
            label.set_position(new_pos)
            new_energy = self.energy()

            delta = new_energy - current_energy

            # Accept if better or with probability exp(-delta/temp)
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_energy = new_energy
            else:
                # Revert
                label.set_position(original_pos)

            # Cool down
            temp *= 0.995

        return current_energy
