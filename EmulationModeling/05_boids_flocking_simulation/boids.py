"""
Emulation/Modeling project implementation.
"""

import numpy as np

class Boid:
    """
    Docstring for Boid.
    """
    def __init__(self, x, y, width, height):
        """
        Docstring for __init__.
        """
        self.position = np.array([x, y], dtype=np.float64)
        angle = np.random.uniform(0, 2 * np.pi)
        self.velocity = np.array([np.cos(angle), np.sin(angle)], dtype=np.float64) * 3
        self.acceleration = np.zeros(2, dtype=np.float64)
        self.max_force = 0.2
        self.max_speed = 4.0
        self.width = width
        self.height = height

    def update(self):
        """
        Docstring for update.
        """
        self.velocity += self.acceleration

        # Limit speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed

        self.position += self.velocity
        self.acceleration[:] = 0

        # Wrap around edges
        self.position[0] %= self.width
        self.position[1] %= self.height

    def apply_force(self, force):
        """
        Docstring for apply_force.
        """
        self.acceleration += force

    def flock(self, boids, separation_dist=25, align_dist=50, cohesion_dist=50):
        """
        Docstring for flock.
        """
        sep = np.zeros(2)
        ali = np.zeros(2)
        coh = np.zeros(2)

        total_sep = 0
        total_ali = 0
        total_coh = 0

        for other in boids:
            if other is self:
                continue

            # Distance wrap-around handling?
            # Simple Euclidean distance for now.
            # Toroidal distance calculation is better but slower O(N^2)
            d = np.linalg.norm(self.position - other.position)

            if d > 0:
                if d < separation_dist:
                    diff = self.position - other.position
                    diff /= d  # Weight by distance
                    sep += diff
                    total_sep += 1

                if d < align_dist:
                    ali += other.velocity
                    total_ali += 1

                if d < cohesion_dist:
                    coh += other.position
                    total_coh += 1

        if total_sep > 0:
            sep /= total_sep
            if np.linalg.norm(sep) > 0:
                sep = (sep / np.linalg.norm(sep)) * self.max_speed - self.velocity
                sep = self._limit(sep, self.max_force)

        if total_ali > 0:
            ali /= total_ali
            if np.linalg.norm(ali) > 0:
                ali = (ali / np.linalg.norm(ali)) * self.max_speed - self.velocity
                ali = self._limit(ali, self.max_force)

        if total_coh > 0:
            coh /= total_coh
            dir_to_target = coh - self.position
            if np.linalg.norm(dir_to_target) > 0:
                dir_to_target = (dir_to_target / np.linalg.norm(dir_to_target)) * self.max_speed - self.velocity
                coh = self._limit(dir_to_target, self.max_force)

        return sep * 1.5 + ali * 1.0 + coh * 1.0

    def _limit(self, vector, max_val):
        """
        Docstring for _limit.
        """
        norm = np.linalg.norm(vector)
        if norm > max_val:
            return (vector / norm) * max_val
        return vector

class Flock:
    """
    Docstring for Flock.
    """
    def __init__(self, count, width, height):
        """
        Docstring for __init__.
        """
        self.boids = [Boid(np.random.rand()*width, np.random.rand()*height, width, height) for _ in range(count)]
        self.width = width
        self.height = height

    def update(self):
        # O(N^2) - optimization possible with QuadTree or spatial hash
        """
        Docstring for update.
        """
        for boid in self.boids:
            force = boid.flock(self.boids)
            boid.apply_force(force)
            boid.update()
