import unittest

import simpy
from elevator_system import Controller, Elevator


class TestElevatorSystem(unittest.TestCase):
    def test_elevator_move(self):
        env = simpy.Environment()
        elev = Elevator(env, 0)

        elev.request_floor(2)  # Go from 0 to 2

        # It takes:
        # 1 tick to wake up/check
        # 2 ticks travel 0->1
        # 2 ticks travel 1->2
        # 2 ticks door open
        # Total ~7 ticks

        env.run(until=10)
        self.assertEqual(elev.current_floor, 2)

    def test_controller_dispatch(self):
        env = simpy.Environment()
        ctrl = Controller(env, num_elevators=2)

        # Elev 0 is at 0. Elev 1 is at 0.
        # Move Elev 1 to 5
        ctrl.elevators[1].current_floor = 5

        # Request at 1 going up. Elev 0 (at 0) is closer than Elev 1 (at 5).
        assigned = ctrl.call_elevator(1, 1)
        self.assertEqual(assigned, 0)

        # Request at 6 going up. Elev 1 (at 5) is closer.
        assigned = ctrl.call_elevator(6, 1)
        self.assertEqual(assigned, 1)


if __name__ == "__main__":
    unittest.main()
