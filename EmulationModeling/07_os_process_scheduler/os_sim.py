class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority

        self.start_time = -1
        self.completion_time = -1
        self.wait_time = 0
        self.turnaround_time = 0

    def is_finished(self):
        return self.remaining_time <= 0

    def __repr__(self):
        return f"P{self.pid}(Arr={self.arrival_time}, Burst={self.burst_time})"


class Scheduler:
    def __init__(self, algorithm="FCFS", quantum=2):
        self.algorithm = algorithm
        self.quantum = quantum
        self.ready_queue = []
        self.current_process = None
        self.time = 0
        self.completed_processes = []
        self.gantt_chart = []  # List of (pid, start, end)

    def add_process(self, process):
        # In a real system, processes are added when time matches arrival.
        # Here we assume the kernel handles moving from new -> ready.
        self.ready_queue.append(process)

    def schedule(self):
        if self.algorithm == "FCFS":
            # Sort by arrival time if not already
            # Actually FCFS just takes front of queue
            if not self.current_process and self.ready_queue:
                self.current_process = self.ready_queue.pop(0)

        elif self.algorithm == "SJF":
            # Shortest Job First (Non-preemptive)
            if not self.current_process and self.ready_queue:
                # Find process with shortest burst
                self.ready_queue.sort(key=lambda p: p.burst_time)
                self.current_process = self.ready_queue.pop(0)

        elif self.algorithm == "RR":
            # Round Robin
            if not self.current_process and self.ready_queue:
                self.current_process = self.ready_queue.pop(0)

            # Preemption logic handled in tick()

        return self.current_process

    def tick(self):
        # Update wait times for processes in ready queue
        for p in self.ready_queue:
            p.wait_time += 1

        if self.current_process:
            if self.current_process.start_time == -1:
                self.current_process.start_time = self.time

            self.current_process.remaining_time -= 1
            self.gantt_chart.append((self.current_process.pid, self.time))

            if self.current_process.is_finished():
                self.current_process.completion_time = self.time + 1
                self.current_process.turnaround_time = (
                    self.current_process.completion_time
                    - self.current_process.arrival_time
                )
                # wait time is turnaround - burst (or accumulated wait)
                # self.current_process.wait_time = self.current_process.turnaround_time - self.current_process.burst_time
                self.completed_processes.append(self.current_process)
                self.current_process = None

            elif self.algorithm == "RR":
                # Check quantum
                time_running = (
                    self.current_process.burst_time
                    - self.current_process.remaining_time
                )
                # If we just finished a quantum (and process not finished)
                # Note: this logic is slightly tricky if we context switch.
                # A better way: track 'current_burst_run'
                pass  # Simplified below

        self.time += 1


class Kernel:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.processes = []
        self.new_processes = []  # Processes that haven't arrived yet

    def load_processes(self, processes):
        self.new_processes = sorted(processes, key=lambda p: p.arrival_time)

    def run(self, max_time=100):
        while self.time < max_time:
            # Check arrivals
            while (
                self.new_processes and self.new_processes[0].arrival_time <= self.time
            ):
                p = self.new_processes.pop(0)
                self.scheduler.ready_queue.append(p)

            # RR specific: Quantum check
            if self.scheduler.algorithm == "RR" and self.scheduler.current_process:
                # Calculate how long current process has been running in THIS slice
                # We need to track slice time in scheduler
                # For simplicity, let's implement RR logic inside tick better
                pass

            proc = self.scheduler.schedule()

            # RR Preemption logic needs to happen after one tick?
            # Or before schedule?
            # Let's put logic in Kernel loop for clarity

            self.scheduler.tick()

            # RR Preemption logic must check state AFTER tick (since tick consumes 1 unit)
            # The tick() function decremented remaining_time and incremented time.

            if self.scheduler.algorithm == "RR":
                current = self.scheduler.current_process
                if current:  # If a process is still running after tick (didn't finish)
                    if not hasattr(self.scheduler, "slice_timer"):
                        self.scheduler.slice_timer = 0

                    self.scheduler.slice_timer += 1

                    if self.scheduler.slice_timer >= self.scheduler.quantum:
                        # Preempt
                        self.scheduler.ready_queue.append(current)
                        self.scheduler.current_process = None
                        self.scheduler.slice_timer = 0
                else:
                    # Process finished or None was running, reset timer
                    self.scheduler.slice_timer = 0

            # Exit if all done
            if (
                not self.new_processes
                and not self.scheduler.ready_queue
                and not self.scheduler.current_process
            ):
                break

    @property
    def time(self):
        return self.scheduler.time
