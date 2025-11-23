package main

import (
	"math"
	"sort"
	"testing"
)

func TestQuantileEstimator(t *testing.T) {
	// Epsilon 0.1 -> error approx 10%
	qe := NewQuantileEstimator(0.1)

	// Insert 1 to 100
	for i := 1; i <= 100; i++ {
		qe.Insert(float64(i))
	}

	// Query Median (0.5)
	// Expected ~50. Error bound +/- 10 (epsilon * N)
	val, err := qe.Query(0.5)
	if err != nil {
		t.Errorf("Query failed: %v", err)
	}
	if math.Abs(val - 50.0) > 10.0 {
		t.Errorf("Query(0.5) = %f, want approx 50 (+/- 10)", val)
	}

	// Query 0.9
	// Expected ~90. Error +/- 10
	val, _ = qe.Query(0.9)
	if math.Abs(val - 90.0) > 10.0 {
		t.Errorf("Query(0.9) = %f, want approx 90 (+/- 10)", val)
	}
}

func TestQuantileEstimatorExact(t *testing.T) {
	// Small epsilon -> more exact
	qe := NewQuantileEstimator(0.01)

	data := []float64{}
	for i := 0; i < 1000; i++ {
		data = append(data, float64(i))
		qe.Insert(float64(i))
	}

	sort.Float64s(data)

	checkQuantile := func(phi float64) {
		got, _ := qe.Query(phi)
		idx := int(phi * 1000)
		if idx >= 1000 { idx = 999 }
		want := data[idx]

		// Allowed error: epsilon * N = 0.01 * 1000 = 10
		if math.Abs(got - want) > 10.0 {
			t.Errorf("Query(%f) = %f, want %f (+/- 10)", phi, got, want)
		}
	}

	checkQuantile(0.1)
	checkQuantile(0.5)
	checkQuantile(0.9)
	checkQuantile(0.99)
}
