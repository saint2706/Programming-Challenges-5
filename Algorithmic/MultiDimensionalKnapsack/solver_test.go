package main

import "testing"

func TestSolveWithDP(t *testing.T) {
	items := []Item{
		{Weights: []int{1, 2}, Value: 3},
		{Weights: []int{2, 1}, Value: 5},
		{Weights: []int{2, 2}, Value: 5},
	}
	capacity := []int{3, 3}

	solution, err := SolveMultiDimensionalKnapsack(items, capacity)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if solution.Value != 8 {
		t.Fatalf("expected value 8, got %d", solution.Value)
	}

	if len(solution.ChosenItems) != 2 {
		t.Fatalf("expected 2 items, got %d", len(solution.ChosenItems))
	}

	expected := map[int]bool{0: true, 1: true}
	for _, idx := range solution.ChosenItems {
		if !expected[idx] {
			t.Fatalf("unexpected item index %d", idx)
		}
	}
}

func TestSolveWithBranchAndBound(t *testing.T) {
	items := []Item{
		{Weights: []int{500, 500}, Value: 100},
		{Weights: []int{1000, 1000}, Value: 190},
		{Weights: []int{1500, 1500}, Value: 200},
	}
	capacity := []int{2000, 2000}

	solution, err := SolveMultiDimensionalKnapsack(items, capacity)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if solution.Value != 300 {
		t.Fatalf("expected value 300, got %d", solution.Value)
	}

	if len(solution.ChosenItems) != 2 {
		t.Fatalf("expected 2 items chosen, got %d", len(solution.ChosenItems))
	}

	expected := map[int]bool{0: true, 2: true}
	for _, idx := range solution.ChosenItems {
		if !expected[idx] {
			t.Fatalf("unexpected item index %d", idx)
		}
	}
}
