package store

import (
	"fmt"
	"math/rand"
	"testing"
	"time"
)

func TestOverlapQueries(t *testing.T) {
	tree := NewIntervalTree()
	base := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	events := []Event{
		{ID: "a", Start: base, End: base.Add(2 * time.Hour)},
		{ID: "b", Start: base.Add(30 * time.Minute), End: base.Add(90 * time.Minute)},
		{ID: "c", Start: base.Add(3 * time.Hour), End: base.Add(4 * time.Hour)},
		{ID: "d", Start: base.Add(2 * time.Hour), End: base.Add(3 * time.Hour)},
	}
	for _, ev := range events {
		tree.Insert(ev)
	}

	overlaps := tree.QueryOverlap(base.Add(45*time.Minute), base.Add(150*time.Minute))
	if len(overlaps) != 3 {
		t.Fatalf("expected 3 overlaps, got %d", len(overlaps))
	}

	ids := map[string]bool{}
	for _, ev := range overlaps {
		ids[ev.ID] = true
	}

	if !ids["a"] || !ids["b"] || !ids["d"] {
		t.Fatalf("expected events a, b, and d in overlap results, got %v", ids)
	}
}

func TestContainmentQueries(t *testing.T) {
	tree := NewIntervalTree()
	base := time.Date(2024, 2, 1, 0, 0, 0, 0, time.UTC)

	container := Event{ID: "container", Start: base.Add(-time.Hour), End: base.Add(5 * time.Hour)}
	nested := Event{ID: "nested", Start: base.Add(time.Hour), End: base.Add(2 * time.Hour)}
	outer := Event{ID: "outer", Start: base.Add(-2 * time.Hour), End: base.Add(-time.Hour)}

	tree.Insert(container)
	tree.Insert(nested)
	tree.Insert(outer)

	results := tree.QueryContaining(base.Add(75*time.Minute), base.Add(90*time.Minute))
	if len(results) != 2 {
		t.Fatalf("expected 2 containing events, got %d", len(results))
	}

	ids := map[string]bool{}
	for _, ev := range results {
		ids[ev.ID] = true
	}
	if !ids["container"] || !ids["nested"] {
		t.Fatalf("expected container and nested to contain the range, got %v", ids)
	}
}

func BenchmarkLargeDatasetOverlap(b *testing.B) {
	tree := NewIntervalTree()
	base := time.Now()
	rand.Seed(42)

	const eventsCount = 200_000
	for i := 0; i < eventsCount; i++ {
		startOffset := time.Duration(rand.Intn(1_000_000)) * time.Millisecond
		duration := time.Duration(rand.Intn(3_600)) * time.Second
		ev := Event{
			ID:    fmt.Sprintf("ev-%d", i),
			Start: base.Add(startOffset),
			End:   base.Add(startOffset + duration),
		}
		tree.Insert(ev)
	}

	queryStart := base.Add(30 * time.Minute)
	queryEnd := queryStart.Add(5 * time.Minute)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		res := tree.QueryOverlap(queryStart, queryEnd)
		if len(res) == 0 {
			b.Fatalf("expected overlaps during benchmark")
		}
	}
}
