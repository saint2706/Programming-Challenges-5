# Temporal Event Store

A data structure for efficiently storing and querying events with time ranges using interval trees.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**Temporal event storage** manages events that occur over time intervals, supporting efficient queries like "find all events overlapping a given time range."

### Interval Tree
- Balanced binary search tree storing intervals
- Each node stores:
  - An interval [start, end]
  - Max endpoint in its subtree
- Enables fast overlap queries

### Operations
1. **Insert**: Add event with time range
2. **Query**: Find all events overlapping [t1, t2]
3. **Point Query**: Find all events active at time t
4. **Delete**: Remove an event

### Use Cases
- Calendar systems (find conflicting meetings)
- Log analysis (events in time window)
- Network monitoring (active connections)
- Game replays (entities present at timestamp)

## 💻 Installation

```bash
go build ./cmd/tes
go test ./store
```

## 🚀 Usage

```go
package main

import (
    "fmt"
    "temporaleventstore/store"
    "time"
)

func main() {
    tree := store.NewIntervalTree()
    
    // Insert events with time ranges
    tree.Insert(Event{
        ID: "meeting1",
        Start: time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC),
        End:   time.Date(2024, 1, 15, 11, 0, 0, 0, time.UTC),
        Data:  "Team standup",
    })
    
    tree.Insert(Event{
        ID: "meeting2",
        Start: time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC),
        End:   time.Date(2024, 1, 15, 11, 30, 0, 0, time.UTC),
        Data:  "Client call",
    })
    
    // Query: Find events between 10:00 and 10:45
    queryStart := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
    queryEnd := time.Date(2024, 1, 15, 10, 45, 0, 0, time.UTC)
    
    events := tree.Query(queryStart, queryEnd)
    fmt.Printf("Found %d overlapping events\n", len(events))
}
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Insert** | $O(\log n)$ | $O(n)$ |
| **Query** | $O(\log n + k)$ | $O(n)$ |
| **Point Query** | $O(\log n + k)$ | $O(n)$ |

Where:
- $n$ = number of events
- $k$ = number of overlapping events found

## Demos

To demonstrate the algorithm, run:

```bash
python main.py
```
