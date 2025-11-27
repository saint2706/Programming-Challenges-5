"""Elevator system model using discrete event simulation with SimPy.

This module simulates an elevator system with multiple elevators using
a SCAN-like scheduling algorithm. Supports configurable number of
elevators, floors, and capacity.
"""
import simpy


class Elevator:
    """Simulates a single elevator with SCAN-like behavior."""

    def __init__(self, env, id, floors=10, capacity=8):
        """Initialize an elevator.

        Args:
            env: SimPy environment.
            id: Unique identifier for this elevator.
            floors: Total number of floors in the building.
            capacity: Maximum passenger capacity.
        """
        self.env = env
        self.id = id
        self.floors = floors
        self.capacity = capacity

        self.current_floor = 0
        self.direction = 0 # 1=up, -1=down, 0=idle
        self.passengers = []

        # Requests: set of floors to stop at
        self.stops = set()

        self.action = env.process(self.run())
        self.door_open_time = 2
        self.travel_time_per_floor = 2

    def request_floor(self, floor):
        """Add a floor to the elevator's stop list."""
        self.stops.add(floor)
        if self.direction == 0:
            if floor > self.current_floor:
                self.direction = 1
            elif floor < self.current_floor:
                self.direction = -1

    def run(self):
        """Main elevator control loop (SimPy process)."""
        while True:
            if not self.stops:
                self.direction = 0
                yield self.env.timeout(1) # Idle check
                continue

            # Determine next target
            # Simple SCAN-like behavior: keep going in direction until no more stops, then switch
            if self.direction == 0:
                 # Should have been set by request_floor, but if cleared:
                 pass

            # Move logic
            if self.current_floor in self.stops:
                # Open doors
                self.stops.remove(self.current_floor)
                yield self.env.timeout(self.door_open_time)

                # Check if we should change direction
                # If moving UP and no stops above, switch to DOWN (if stops below)
                if self.direction == 1 and not any(f > self.current_floor for f in self.stops):
                    if any(f < self.current_floor for f in self.stops):
                        self.direction = -1
                    else:
                        self.direction = 0
                elif self.direction == -1 and not any(f < self.current_floor for f in self.stops):
                    if any(f > self.current_floor for f in self.stops):
                        self.direction = 1
                    else:
                        self.direction = 0

            if self.direction != 0:
                yield self.env.timeout(self.travel_time_per_floor)
                self.current_floor += self.direction

class Controller:
    """Elevator dispatch controller using nearest-elevator heuristic."""

    def __init__(self, env, num_elevators=2, floors=10):
        """Initialize the controller with multiple elevators.

        Args:
            env: SimPy environment.
            num_elevators: Number of elevators to manage.
            floors: Total number of floors.
        """
        self.elevators = [Elevator(env, i, floors) for i in range(num_elevators)]

    def call_elevator(self, floor, direction):
        """Dispatch the best elevator to answer a hall call.

        Args:
            floor: Floor where the call originated.
            direction: Requested direction (1=up, -1=down).

        Returns:
            int: ID of the dispatched elevator.
        """
        # Dispatch logic: find best elevator
        # Simple heuristic: find nearest elevator moving in same direction or idle
        best_elevator = None
        min_dist = 999

        for elev in self.elevators:
            dist = abs(elev.current_floor - floor)
            score = 999

            if elev.direction == 0:
                score = dist
            elif elev.direction == 1 and direction == 1 and floor >= elev.current_floor:
                score = dist
            elif elev.direction == -1 and direction == -1 and floor <= elev.current_floor:
                score = dist

            if score < min_dist:
                min_dist = score
                best_elevator = elev

        if best_elevator is None:
            best_elevator = self.elevators[0] # Fallback

        best_elevator.request_floor(floor)
        return best_elevator.id
