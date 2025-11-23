from os_sim import Process, Scheduler, Kernel

def print_stats(processes):
    print(f"{'PID':<5} {'Arr':<5} {'Burst':<5} {'Wait':<5} {'TA':<5}")
    total_wait = 0
    total_ta = 0
    for p in processes:
        print(f"{p.pid:<5} {p.arrival_time:<5} {p.burst_time:<5} {p.wait_time:<5} {p.turnaround_time:<5}")
        total_wait += p.wait_time
        total_ta += p.turnaround_time

    n = len(processes)
    print(f"\nAvg Wait: {total_wait/n:.2f}")
    print(f"Avg TA:   {total_ta/n:.2f}")

def main():
    procs = [
        Process(1, 0, 5),
        Process(2, 1, 3),
        Process(3, 2, 8),
        Process(4, 3, 6)
    ]

    print("--- FCFS ---")
    sched = Scheduler("FCFS")
    kernel = Kernel(sched)
    # Clone procs
    kernel.load_processes([Process(p.pid, p.arrival_time, p.burst_time) for p in procs])
    kernel.run()
    print_stats(sched.completed_processes)

    print("\n--- SJF ---")
    sched = Scheduler("SJF")
    kernel = Kernel(sched)
    kernel.load_processes([Process(p.pid, p.arrival_time, p.burst_time) for p in procs])
    kernel.run()
    print_stats(sched.completed_processes)

    print("\n--- RR (Q=2) ---")
    sched = Scheduler("RR", quantum=2)
    kernel = Kernel(sched)
    kernel.load_processes([Process(p.pid, p.arrival_time, p.burst_time) for p in procs])
    kernel.run()
    print_stats(sched.completed_processes)

if __name__ == "__main__":
    main()
