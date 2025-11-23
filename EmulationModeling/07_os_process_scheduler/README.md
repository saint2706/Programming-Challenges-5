# Operating System Process Scheduler

A simulator for CPU scheduling algorithms including FCFS, SJF, and Round Robin with performance analysis.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Scheduling Algorithms](#scheduling-algorithms)
- [Metrics](#metrics)

## 🧠 Theory

### Process Scheduling
The OS kernel decides which process runs on the CPU:
- **Ready Queue**: Processes waiting for CPU
- **Context Switch**: Saving/restoring process state
- **Time Quantum**: Time slice for each process (Round Robin)
- **Preemption**: Interrupting running process

### Performance Goals
- **Minimize Wait Time**: Time in ready queue
- **Minimize Turnaround Time**: Completion time - arrival time
- **Maximize Throughput**: Processes completed per time unit
- **Fairness**: All processes get CPU time

## 💻 Installation

Requires Python 3.8+ (no external dependencies):
```bash
cd EmulationModeling/07_os_process_scheduler
python main.py
```

## 🚀 Usage

### Running Simulation
```bash
python main.py
```

Output compares three scheduling algorithms:
```
--- FCFS ---
PID   Arr   Burst Wait  TA
1     0     5     0     5
2     1     3     4     7
3     2     8     7     15
4     3     6     12    18

Avg Wait: 5.75
Avg TA:   11.25
```

## 📊 Scheduling Algorithms

### FCFS (First-Come-First-Served)
- **Non-preemptive**: Process runs to completion
- **Simple**: FIFO queue
- **Problem**: Convoy effect (short processes wait for long ones)

### SJF (Shortest Job First)
- **Non-preemptive**: Shortest burst time goes first
- **Optimal**: Minimizes average wait time
- **Problem**: Requires knowing burst time (not realistic)
- **Starvation**: Long processes may never run

### Round Robin (RR)
- **Preemptive**: Each process gets fixed time quantum
- **Fair**: All processes make progress
- **Time Quantum**: Trade-off between responsiveness and overhead
  - Too small: High context switch overhead
  - Too large: Approaches FCFS

## 📈 Metrics

### Wait Time
Time spent in ready queue before first execution

### Turnaround Time
Total time from arrival to completion
```
Turnaround Time = Completion Time - Arrival Time
                = Wait Time + Burst Time
```

### Response Time
Time from arrival to first execution (important for interactive systems)

## ✨ Features

- Three major scheduling algorithms
- Detailed statistics per process
- Average performance metrics
- Process timing visualization
- Configurable time quantum for RR
