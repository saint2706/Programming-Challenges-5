package main

import "testing"

func sampleProblem() *Problem {
	courses := []Course{
		{Name: "Math", Size: 30, Conflicts: []string{"Physics"}},
		{Name: "Physics", Size: 25, Conflicts: []string{"Math"}},
		{Name: "History", Size: 20, Conflicts: nil},
	}
	rooms := []Room{{Name: "R1", Capacity: 40}, {Name: "R2", Capacity: 20}}
	timeSlots := []string{"9AM", "11AM"}
	return NewProblem(courses, rooms, timeSlots)
}

func TestConflictDetection(t *testing.T) {
	p := sampleProblem()
	assignment := map[string]Placement{
		"Math":    {Room: "R1", Time: "9AM"},
		"Physics": {Room: "R2", Time: "9AM"},
		"History": {Room: "R1", Time: "11AM"},
	}

	if err := p.ValidateAssignment(assignment); err == nil {
		t.Fatalf("expected conflict validation to fail")
	}
}

func TestSolverFindsValidTimetable(t *testing.T) {
	p := sampleProblem()
	solution, err := p.Solve(false)
	if err != nil {
		t.Fatalf("solver failed: %v", err)
	}
	if err := p.ValidateAssignment(solution); err != nil {
		t.Fatalf("invalid solution: %v", err)
	}
}

func TestCapacityRespected(t *testing.T) {
	courses := []Course{
		{Name: "Large", Size: 35, Conflicts: nil},
		{Name: "Small", Size: 15, Conflicts: nil},
	}
	rooms := []Room{{Name: "Big", Capacity: 40}, {Name: "Tiny", Capacity: 20}}
	timeSlots := []string{"Morning"}
	p := NewProblem(courses, rooms, timeSlots)

	solution, err := p.Solve(false)
	if err != nil {
		t.Fatalf("solver failed: %v", err)
	}

	if placement := solution["Large"]; placement.Room != "Big" {
		t.Fatalf("expected Large course to use room Big, got %v", placement.Room)
	}
}
