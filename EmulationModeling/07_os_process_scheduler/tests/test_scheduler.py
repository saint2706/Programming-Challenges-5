"""
Emulation/Modeling project implementation.
"""

import unittest
from os_sim import Process, Scheduler, Kernel

class TestScheduler(unittest.TestCase):
    """
    Docstring for TestScheduler.
    """
    def test_fcfs(self):
        # P1: 0, 5
        # P2: 2, 2
        """
        Docstring for test_fcfs.
        """
        p1 = Process(1, 0, 5)
        p2 = Process(2, 2, 2)

        sched = Scheduler("FCFS")
        kernel = Kernel(sched)
        kernel.load_processes([p1, p2])
        kernel.run()

        # P1 runs 0-5. TA = 5-0 = 5. Wait = 0.
        # P2 arrives 2. Wait until 5. Runs 5-7. TA = 7-2 = 5. Wait = 5-2 = 3.

        cp = sorted(sched.completed_processes, key=lambda p: p.pid)
        self.assertEqual(cp[0].turnaround_time, 5)
        self.assertEqual(cp[0].wait_time, 0)

        self.assertEqual(cp[1].turnaround_time, 5)
        self.assertEqual(cp[1].wait_time, 3)

    def test_sjf(self):
        # P1: 0, 5
        # P2: 1, 2
        # P3: 2, 1
        # At t=0, P1 starts. Runs to 5.
        # At t=5, P2(2) and P3(1) are ready. SJF picks P3.
        # P3 runs 5-6.
        # P2 runs 6-8.

        """
        Docstring for test_sjf.
        """
        p1 = Process(1, 0, 5)
        p2 = Process(2, 1, 2)
        p3 = Process(3, 2, 1)

        sched = Scheduler("SJF")
        kernel = Kernel(sched)
        kernel.load_processes([p1, p2, p3])
        kernel.run()

        cp = {p.pid: p for p in sched.completed_processes}

        # P1
        self.assertEqual(cp[1].completion_time, 5)

        # P3
        self.assertEqual(cp[3].completion_time, 6)

        # P2
        self.assertEqual(cp[2].completion_time, 8)

    def test_rr(self):
        # P1: 0, 4. Q=2.
        # 0-2: P1. Rem=2.
        # 2-4: P1. Rem=0. Finished at 4.

        """
        Docstring for test_rr.
        """
        p1 = Process(1, 0, 4)
        sched = Scheduler("RR", quantum=2)
        kernel = Kernel(sched)
        kernel.load_processes([p1])
        kernel.run()

        self.assertEqual(sched.completed_processes[0].completion_time, 4)

if __name__ == '__main__':
    unittest.main()
