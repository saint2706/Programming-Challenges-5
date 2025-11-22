package turnpenaltyrouting

import "testing"

func TestPenaltyInfluencesPathChoice(t *testing.T) {
	edges := []Edge{
		{ID: "e1", From: "A", To: "B", Cost: 1},
		{ID: "e2", From: "B", To: "C", Cost: 1},
		{ID: "e3", From: "A", To: "C", Cost: 3},
	}
	g, err := NewGraph(edges)
	if err != nil {
		t.Fatalf("failed to build graph: %v", err)
	}
	penalties := NewTurnPenalties()
	penalties.SetPenalty("e1", "e2", 3) // makes A->B->C cost 5

	res, err := ShortestPath(g, penalties, "A", "C", nil)
	if err != nil {
		t.Fatalf("search failed: %v", err)
	}
	if res.Cost != 3 {
		t.Fatalf("expected cost 3 via direct edge, got %v", res.Cost)
	}
	if len(res.Path) != 1 || res.Path[0].ID != "e3" {
		t.Fatalf("expected direct edge e3, got %+v", res.Path)
	}
}

func TestForbiddenTurn(t *testing.T) {
	edges := []Edge{
		{ID: "e1", From: "A", To: "B", Cost: 1},
		{ID: "e2", From: "B", To: "C", Cost: 1},
		{ID: "e3", From: "B", To: "D", Cost: 1},
		{ID: "e4", From: "D", To: "C", Cost: 1},
	}
	g, err := NewGraph(edges)
	if err != nil {
		t.Fatalf("failed to build graph: %v", err)
	}
	penalties := NewTurnPenalties()
	penalties.ForbidTurn("e1", "e2")

	res, err := ShortestPath(g, penalties, "A", "C", nil)
	if err != nil {
		t.Fatalf("search failed: %v", err)
	}
	expectedCost := 3.0 // A->B (1) + B->D (1) + D->C (1)
	if res.Cost != expectedCost {
		t.Fatalf("expected cost %.1f avoiding forbidden turn, got %v", expectedCost, res.Cost)
	}
	gotIDs := []string{res.Path[0].ID, res.Path[1].ID, res.Path[2].ID}
	wantIDs := []string{"e1", "e3", "e4"}
	for i := range wantIDs {
		if gotIDs[i] != wantIDs[i] {
			t.Fatalf("expected path %v, got %v", wantIDs, gotIDs)
		}
	}
}

func TestPathReconstructionWithTurnPenalties(t *testing.T) {
	edges := []Edge{
		{ID: "e1", From: "S", To: "A", Cost: 2},
		{ID: "e2", From: "A", To: "G", Cost: 2},
		{ID: "e3", From: "S", To: "B", Cost: 1},
		{ID: "e4", From: "B", To: "G", Cost: 10},
	}
	g, err := NewGraph(edges)
	if err != nil {
		t.Fatalf("failed to build graph: %v", err)
	}
	penalties := NewTurnPenalties()
	penalties.SetPenalty("e1", "e2", -0.5) // reward this turn to ensure preference

	res, err := ShortestPath(g, penalties, "S", "G", nil)
	if err != nil {
		t.Fatalf("search failed: %v", err)
	}
	expectedCost := 3.5 // 2 + 2 - 0.5
	if res.Cost != expectedCost {
		t.Fatalf("expected cost %.1f, got %v", expectedCost, res.Cost)
	}
	if len(res.Path) != 2 || res.Path[0].ID != "e1" || res.Path[1].ID != "e2" {
		t.Fatalf("unexpected path reconstruction: %+v", res.Path)
	}
}
