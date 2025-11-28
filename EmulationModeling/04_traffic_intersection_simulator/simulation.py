import random

import simpy


class TrafficIntersection:
    def __init__(self, env, green_duration=10, yellow_duration=2, red_duration=10):
        self.env = env
        self.green_duration = green_duration
        self.yellow_duration = yellow_duration
        self.red_duration = red_duration

        # Directions: NS (North-South) and EW (East-West)
        # State: "green", "yellow", "red"
        self.lights = {"NS": "green", "EW": "red"}

        # Queues for cars waiting
        self.lanes = {
            "NS": simpy.Resource(
                env, capacity=1
            ),  # Capacity controls flow rate? No, capacity 1 means 1 car passing intersection at a time per lane
            "EW": simpy.Resource(env, capacity=1),
        }

        self.queue_lengths = {"NS": 0, "EW": 0}
        self.stats = {"arrived": 0, "crossed": 0, "total_wait_time": 0}

        self.action = env.process(self.run())

    def run(self):
        while True:
            # NS Green, EW Red
            self.lights["NS"] = "green"
            self.lights["EW"] = "red"
            yield self.env.timeout(self.green_duration)

            # NS Yellow
            self.lights["NS"] = "yellow"
            yield self.env.timeout(self.yellow_duration)

            # NS Red, EW Green (Safety buffer optional, but simplified here)
            self.lights["NS"] = "red"
            self.lights["EW"] = "green"
            yield self.env.timeout(
                self.green_duration
            )  # Use same duration for EW for now

            # EW Yellow
            self.lights["EW"] = "yellow"
            yield self.env.timeout(self.yellow_duration)


def car_generator(env, intersection, direction, arrival_rate):
    """Generates cars for a specific direction."""
    while True:
        yield env.timeout(random.expovariate(arrival_rate))
        intersection.stats["arrived"] += 1
        env.process(car(env, intersection, direction))


def car(env, intersection, direction):
    arrival_time = env.now
    intersection.queue_lengths[direction] += 1

    # Request access to the intersection lane
    # Cars can only pass if light is green.
    # We model this by waiting for the light AND the resource.

    with intersection.lanes[direction].request() as req:
        yield req  # Wait for turn at stop line

        # Wait for Green light
        while intersection.lights[direction] != "green":
            yield env.timeout(1)  # Check every second

        # Passing through
        intersection.queue_lengths[direction] -= 1

        # Time to cross intersection
        yield env.timeout(2)

        intersection.stats["crossed"] += 1
        intersection.stats["total_wait_time"] += env.now - arrival_time


def run_simulation(duration=200):
    env = simpy.Environment()
    intersection = TrafficIntersection(env)

    # Traffic flow NS (higher volume)
    env.process(car_generator(env, intersection, "NS", arrival_rate=0.2))
    # Traffic flow EW (lower volume)
    env.process(car_generator(env, intersection, "EW", arrival_rate=0.1))

    env.run(until=duration)

    return intersection.stats
