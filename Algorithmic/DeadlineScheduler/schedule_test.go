package deadlinescheduler

import "testing"

func TestDPBeatsGreedyWhenLongHighPenaltyJobExists(t *testing.T) {
	jobs := []Job{
		{ID: 1, Deadline: 4, Duration: 4, Penalty: 100},
		{ID: 2, Deadline: 5, Duration: 2, Penalty: 99},
		{ID: 3, Deadline: 5, Duration: 2, Penalty: 98},
	}

	greedy, err := GreedySchedule(jobs)
	if err != nil {
		t.Fatalf("greedy schedule failed: %v", err)
	}
	if greedy.TotalPenalty != 197 {
		t.Fatalf("unexpected greedy penalty: got %d", greedy.TotalPenalty)
	}

	optimal, err := DPSchedule(jobs)
	if err != nil {
		t.Fatalf("dp schedule failed: %v", err)
	}
	if optimal.TotalPenalty != 100 {
		t.Fatalf("dp should drop only job 1: got penalty %d", optimal.TotalPenalty)
	}
	if len(optimal.Order) != 2 || optimal.Order[0].ID != 2 || optimal.Order[1].ID != 3 {
		t.Fatalf("unexpected optimal order: %+v", optimal.Order)
	}
}

func TestDPHandlesImpossibleDeadlines(t *testing.T) {
	jobs := []Job{
		{ID: 1, Deadline: 1, Duration: 3, Penalty: 5},
		{ID: 2, Deadline: 2, Duration: 1, Penalty: 7},
	}

	res, err := DPSchedule(jobs)
	if err != nil {
		t.Fatalf("dp schedule failed: %v", err)
	}

	if res.TotalPenalty != 5 {
		t.Fatalf("expected to drop job 1 only: got %d", res.TotalPenalty)
	}
	if len(res.Order) != 1 || res.Order[0].ID != 2 {
		t.Fatalf("unexpected order: %+v", res.Order)
	}
}

func TestGreedyAndDPAgreeOnTies(t *testing.T) {
	jobs := []Job{
		{ID: 1, Deadline: 2, Duration: 1, Penalty: 5},
		{ID: 2, Deadline: 2, Duration: 1, Penalty: 5},
		{ID: 3, Deadline: 2, Duration: 1, Penalty: 5},
	}

	greedy, err := GreedySchedule(jobs)
	if err != nil {
		t.Fatalf("greedy schedule failed: %v", err)
	}
	optimal, err := DPSchedule(jobs)
	if err != nil {
		t.Fatalf("dp schedule failed: %v", err)
	}

	if greedy.TotalPenalty != 5 {
		t.Fatalf("one job should be dropped: got %d", greedy.TotalPenalty)
	}
	if optimal.TotalPenalty != 5 {
		t.Fatalf("dp should match greedy for uniform penalties: got %d", optimal.TotalPenalty)
	}
	if len(optimal.Order) != 2 || len(greedy.Order) != 2 {
		t.Fatalf("expected two scheduled jobs: dp=%d greedy=%d", len(optimal.Order), len(greedy.Order))
	}
}

func TestEmptyJobsError(t *testing.T) {
	if _, err := DPSchedule(nil); err == nil {
		t.Fatalf("expected error for empty input")
	}
	if _, err := GreedySchedule(nil); err == nil {
		t.Fatalf("expected error for empty input")
	}
}
