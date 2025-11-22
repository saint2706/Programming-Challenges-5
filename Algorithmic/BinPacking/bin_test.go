package binpacking

import (
	"reflect"
	"testing"
)

func TestFirstFitCounts(t *testing.T) {
	items := []float64{4, 8, 1, 4, 2, 1}
	bins, err := FirstFit(10, items)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got := len(bins); got != 2 {
		t.Fatalf("expected 2 bins, got %d", got)
	}
}

func TestBestFitMatchesFirstFitDecreasing(t *testing.T) {
	items := []float64{5, 5, 4, 4, 2, 2}
	best, err := BestFit(6, items)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	ffd, err := FirstFitDecreasing(6, items)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(best) != len(ffd) {
		t.Fatalf("heuristics produced different bin counts: %d vs %d", len(best), len(ffd))
	}
}

func TestFirstFitDecreasingImproves(t *testing.T) {
	items := []float64{2, 5, 4, 7, 1, 3, 8, 2}
	ff, err := FirstFit(10, items)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	ffd, err := FirstFitDecreasing(10, items)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ffd) > len(ff) {
		t.Fatalf("FFD should not use more bins than FF: %d vs %d", len(ffd), len(ff))
	}
}

func TestShelfFirstFit(t *testing.T) {
	rects := []Rect{{4, 2}, {4, 2}, {3, 1}, {3, 1}, {2, 1}}
	bins, err := ShelfFirstFit(8, 4, rects)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(bins) != 1 {
		t.Fatalf("expected all rectangles to fit in one bin, got %d", len(bins))
	}
	expectedShelves := []int{2, 3}
	gotShelves := []int{len(bins[0].Shelves[0].Items), len(bins[0].Shelves[1].Items)}
	if !reflect.DeepEqual(expectedShelves, gotShelves) {
		t.Fatalf("unexpected shelf distribution: %v", gotShelves)
	}
}
