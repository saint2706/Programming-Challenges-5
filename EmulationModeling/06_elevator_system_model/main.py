import simpy
import random
from elevator_system import Controller

def person_generator(env, controller, floors=10):
    i = 0
    while True:
        yield env.timeout(random.expovariate(0.1)) # Arrival rate
        i += 1

        start_floor = random.randint(0, floors-1)
        target_floor = random.randint(0, floors-1)
        while target_floor == start_floor:
            target_floor = random.randint(0, floors-1)

        direction = 1 if target_floor > start_floor else -1

        print(f"[{env.now:.1f}] Person {i} calls from {start_floor} going to {target_floor}")

        # Call elevator to start floor
        elev_id = controller.call_elevator(start_floor, direction)

        # In a real sim, we would wait for elevator to arrive, then request target.
        # Here we simplify: when calling, we assume the person queues the destination request
        # once they get in.
        # But `call_elevator` only registers the pickup.
        # We need a callback or process to register the drop-off request when elevator arrives.
        env.process(person_behavior(env, controller.elevators[elev_id], start_floor, target_floor))

def person_behavior(env, elevator, start, target):
    # Wait for elevator to arrive at start
    while elevator.current_floor != start:
        yield env.timeout(1)

    # Elevator arrived. Add destination.
    elevator.request_floor(target)
    # print(f"[{env.now:.1f}] Person entered Elev {elevator.id} at {start}, pressed {target}")

def main():
    env = simpy.Environment()
    controller = Controller(env, num_elevators=2, floors=10)

    env.process(person_generator(env, controller))

    env.run(until=200)

if __name__ == "__main__":
    main()
