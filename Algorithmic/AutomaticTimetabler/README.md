# Automatic Timetabler

An automatic timetabling system that schedules courses, rooms, and time slots while avoiding conflicts using constraint satisfaction and graph coloring.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Timetabling** assigns courses to time slots and rooms while satisfying constraints.

### Problem as Graph Coloring

- **Nodes**: Courses
- **Edges**: Conflicts (same instructor, shared students, etc.)
- **Colors**: Time slots
- **Goal**: Assign colors such that no adjacent nodes share a color

This is the **graph coloring problem** (NP-complete).

### Constraints

1. **Hard constraints**: Must be satisfied
   - No instructor teaches multiple courses simultaneously
   - Room capacity sufficient
   - No student has overlapping classes
2. **Soft constraints**: Prefer to satisfy
   - Minimize gaps in student schedules
   - Prefer certain time slots
   - Balanced distribution across days

### Solution Approaches

1. **Backtracking**: Try assignments, backtrack on conflict
2. **Greedy with heuristics**:
   - Largest degree first (most constrained)
   - Saturation degree (most colors used by neighbors)
3. **Simulated annealing**: Probabilistic improvement

## 💻 Installation

```bash
go build ./main.go
go test
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "automatictimetabler"
)

func main() {
    // Define courses
    courses := []Course{
        {ID: "CS101", Instructor: "Smith", Students: []string{"A", "B"}},
        {ID: "CS102", Instructor: "Jones", Students: []string{"A", "C"}},
        {ID: "CS201", Instructor: "Smith", Students: []string{"B", "C"}},
    }

    // Define time slots
    slots := []TimeSlot{
        {Day: "Mon", Time: "9:00"},
        {Day: "Mon", Time: "10:00"},
        {Day: "Tue", Time: "9:00"},
    }

    // Create timetabler
    timetabler := NewTimetabler(courses, slots)

    // Generate timetable
    schedule, ok := timetabler.Generate()
    if ok {
        for course, slot := range schedule {
            fmt.Printf("%s: %s %s\n", course, slot.Day, slot.Time)
        }
    } else {
        fmt.Println("No valid schedule found")
    }
}
```

## 📊 Complexity Analysis

| Approach                | Time Complexity          |
| :---------------------- | :----------------------- |
| **Backtracking**        | $O(k^n)$ worst case      |
| **Greedy**              | $O(n^2)$                 |
| **Simulated Annealing** | $O(iterations \times n)$ |

Where:

- $n$ = number of courses
- $k$ = number of time slots

In practice, backtracking with good heuristics performs well for moderately sized problems.
