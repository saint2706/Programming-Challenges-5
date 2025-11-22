package deadlinescheduler

import (
	"container/heap"
	"errors"
	"fmt"
	"sort"
)

// Job represents a schedulable task.
type Job struct {
	ID       int
	Deadline int
	Duration int
	Penalty  int
}

// ScheduleResult contains the chosen ordering and penalty.
type ScheduleResult struct {
	Order        []Job
	TotalPenalty int
}

// GreedySchedule returns a near-optimal schedule using a priority-queue heuristic.
// It sorts jobs by deadline and discards the currently cheapest-penalty jobs when
// the cumulative duration exceeds the active deadline.
func GreedySchedule(jobs []Job) (ScheduleResult, error) {
	if len(jobs) == 0 {
		return ScheduleResult{}, errors.New("no jobs provided")
	}

	sorted := append([]Job(nil), jobs...)
	sort.SliceStable(sorted, func(i, j int) bool {
		if sorted[i].Deadline == sorted[j].Deadline {
			return sorted[i].ID < sorted[j].ID
		}
		return sorted[i].Deadline < sorted[j].Deadline
	})

	h := &penaltyMinHeap{}
	totalDuration := 0
	droppedPenalty := 0

	for _, job := range sorted {
		heap.Push(h, job)
		totalDuration += job.Duration

		// Ensure we can finish by the current job's deadline; drop cheapest-penalty jobs first.
		for totalDuration > job.Deadline && h.Len() > 0 {
			removed := heap.Pop(h).(Job)
			totalDuration -= removed.Duration
			droppedPenalty += removed.Penalty
		}
	}

	remaining := h.data
	sort.SliceStable(remaining, func(i, j int) bool {
		if remaining[i].Deadline == remaining[j].Deadline {
			return remaining[i].ID < remaining[j].ID
		}
		return remaining[i].Deadline < remaining[j].Deadline
	})

	return ScheduleResult{Order: remaining, TotalPenalty: droppedPenalty}, nil
}

// DPSchedule computes the optimal schedule using dynamic programming.
// The algorithm runs in O(n * sumDuration) time and guarantees minimal penalty.
func DPSchedule(jobs []Job) (ScheduleResult, error) {
	if len(jobs) == 0 {
		return ScheduleResult{}, errors.New("no jobs provided")
	}

	sorted := append([]Job(nil), jobs...)
	sort.SliceStable(sorted, func(i, j int) bool {
		if sorted[i].Deadline == sorted[j].Deadline {
			return sorted[i].ID < sorted[j].ID
		}
		return sorted[i].Deadline < sorted[j].Deadline
	})

	sumDur := 0
	for _, job := range sorted {
		sumDur += job.Duration
	}

	const inf = int(^uint(0) >> 1)
	dp := make([][]int, len(sorted)+1)
	choice := make([][]decision, len(sorted)+1)
	dp[0] = make([]int, sumDur+1)
	choice[0] = make([]decision, sumDur+1)
	for t := 1; t <= sumDur; t++ {
		dp[0][t] = inf
	}

	for i, job := range sorted {
		dp[i+1] = make([]int, sumDur+1)
		choice[i+1] = make([]decision, sumDur+1)
		for t := 0; t <= sumDur; t++ {
			dp[i+1][t] = inf
		}

		for t := 0; t <= sumDur; t++ {
			if dp[i][t] == inf {
				continue
			}

			// Option 1: skip the job (incur penalty)
			skipPenalty := dp[i][t] + job.Penalty
			if skipPenalty < dp[i+1][t] {
				dp[i+1][t] = skipPenalty
				choice[i+1][t] = decision{prevTime: t, take: false}
			}

			// Option 2: take the job if it fits before its deadline
			finish := t + job.Duration
			if finish <= job.Deadline && dp[i][t] < dp[i+1][finish] {
				dp[i+1][finish] = dp[i][t]
				choice[i+1][finish] = decision{prevTime: t, take: true}
			}
		}
	}

	bestTime := 0
	bestPenalty := inf
	for t := 0; t <= sumDur; t++ {
		if dp[len(sorted)][t] < bestPenalty {
			bestPenalty = dp[len(sorted)][t]
			bestTime = t
		}
	}

	if bestPenalty == inf {
		return ScheduleResult{}, fmt.Errorf("no feasible schedule found")
	}

	order := make([]Job, 0)
	time := bestTime
	for i := len(sorted); i > 0; i-- {
		dec := choice[i][time]
		if dec.take {
			order = append(order, sorted[i-1])
		}
		time = dec.prevTime
	}

	// reverse to obtain processing order respecting deadlines
	for i, j := 0, len(order)-1; i < j; i, j = i+1, j-1 {
		order[i], order[j] = order[j], order[i]
	}

	return ScheduleResult{Order: order, TotalPenalty: bestPenalty}, nil
}

type decision struct {
	prevTime int
	take     bool
}

type penaltyMinHeap struct {
	data []Job
}

func (h penaltyMinHeap) Len() int { return len(h.data) }

func (h penaltyMinHeap) Less(i, j int) bool { return h.data[i].Penalty < h.data[j].Penalty }

func (h penaltyMinHeap) Swap(i, j int) { h.data[i], h.data[j] = h.data[j], h.data[i] }

func (h *penaltyMinHeap) Push(x interface{}) {
	h.data = append(h.data, x.(Job))
}

func (h *penaltyMinHeap) Pop() interface{} {
	old := h.data
	n := len(old)
	item := old[n-1]
	h.data = old[0 : n-1]
	return item
}
