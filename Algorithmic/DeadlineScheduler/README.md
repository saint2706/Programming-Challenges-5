# Scheduler with Deadlines & Penalties

A scheduler that handles jobs with deadlines and penalties, optimizing to minimize total penalty for missed deadlines.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Job scheduling with deadlines** assigns jobs to time slots to minimize penalties for late completion.

### Problem Definition
- Each job has a deadline and a penalty for missing it
- Each time slot can hold one job
- Goal: Minimize total penalty

### Algorithm
1. **Sort jobs** by penalty (descending) - do high-penalty jobs first
2. **Greedy assignment**: For each job, try to schedule it as late as possible before its deadline
3. **Disjoint Set Union (DSU)**: Efficiently find available time slots

### Why This Works
By processing jobs in penalty order and scheduling each as late as possible, we maximize flexibility for future jobs.

## 💻 Installation

Ensure you have Go 1.21+ installed.

```bash
go build ./cmd/deadlinescheduler
```

### Running Tests

```bash
go test ./...
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "github.com/yourusername/deadlinescheduler"
)

func main() {
    jobs := []Job{
        {ID: 1, Deadline: 2, Penalty: 40},
        {ID: 2, Deadline: 1, Penalty: 35},
        {ID: 3, Deadline: 2, Penalty: 30},
        {ID: 4, Deadline: 1, Penalty: 25},
    }
    
    scheduler := NewScheduler(jobs)
    schedule, penalty := scheduler.MinimizePenalty()
    
    fmt.Printf("Schedule: %v\n", schedule)
    fmt.Printf("Total penalty: %d\n", penalty)
}
```

### Example Output

```
Schedule: [Job 2, Job 1]
Total penalty: 55
Explanation: Jobs 3 and 4 missed deadlines (30 + 25 = 55)
```

## 📊 Complexity Analysis

| Operation | Time Complexity |
| :--- | :--- |
| **Schedule (with DSU)** | $O(n \log n)$ |
| **Schedule (naive)** | $O(n^2)$ |

Where $n$ is the number of jobs.

## Demos

To demonstrate the algorithm, run:

```bash
go run .
```
