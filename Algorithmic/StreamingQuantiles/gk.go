package main

import (
	"fmt"
	"sort"
)

// Tuple represents a sample in the summary data structure (Greenwald-Khanna).
type Tuple struct {
	v     float64
	g     int
	delta int
}

// QuantileEstimator implements the Greenwald-Khanna algorithm for epsilon-approximate quantiles.
type QuantileEstimator struct {
	summary []Tuple
	epsilon float64
	n       int
}

// NewQuantileEstimator creates a new estimator.
func NewQuantileEstimator(epsilon float64) *QuantileEstimator {
	return &QuantileEstimator{
		summary: []Tuple{},
		epsilon: epsilon,
		n:       0,
	}
}

// Insert adds a value to the stream.
func (qe *QuantileEstimator) Insert(v float64) {
	qe.n++

	idx := sort.Search(len(qe.summary), func(i int) bool {
		return qe.summary[i].v >= v
	})

	var t Tuple
	if idx == 0 || idx == len(qe.summary) {
		t = Tuple{v: v, g: 1, delta: 0}
	} else {
		delta := int(2 * qe.epsilon * float64(qe.n))
		t = Tuple{v: v, g: 1, delta: delta}
	}

	qe.summary = append(qe.summary, Tuple{})
	copy(qe.summary[idx+1:], qe.summary[idx:])
	qe.summary[idx] = t

	if qe.n % (1 + int(1.0/qe.epsilon)) == 0 {
		qe.Compress()
	}
}

// Compress merges tuples.
func (qe *QuantileEstimator) Compress() {
	limit := int(2 * qe.epsilon * float64(qe.n))

	// Iterate backwards. Maintain index of the "right neighbor" that we can merge into.
	rightIdx := len(qe.summary) - 1

	for i := len(qe.summary) - 2; i >= 0; i-- {
		t_curr := qe.summary[i]
		t_right := qe.summary[rightIdx]

		// Condition: g_curr + g_right + delta_right <= limit
		if t_curr.g + t_right.g + t_right.delta <= limit {
			// Merge current into right.
			qe.summary[rightIdx].g += t_curr.g
			qe.summary[i].g = -1 // Mark deleted
			// rightIdx remains the same (it absorbed i)
		} else {
			// Cannot merge. Current becomes the new right neighbor for i-1.
			rightIdx = i
		}
	}

	newSummary := make([]Tuple, 0, len(qe.summary))
	for _, t := range qe.summary {
		if t.g != -1 {
			newSummary = append(newSummary, t)
		}
	}
	qe.summary = newSummary
}

// Query returns the estimated value for quantile phi.
func (qe *QuantileEstimator) Query(phi float64) (float64, error) {
	if len(qe.summary) == 0 {
		return 0, fmt.Errorf("empty stream")
	}

	targetRank := int(phi * float64(qe.n))
	margin := int(qe.epsilon * float64(qe.n)) // This is epsilon * N

	// Find min i such that r_max(i) > targetRank + epsilon*N
	// Return v_{i-1}

	currentRankMin := 0
	for i, t := range qe.summary {
		currentRankMin += t.g
		rMax := currentRankMin + t.delta

		if rMax > targetRank + margin {
			if i == 0 {
				return t.v, nil // Should not happen for typical phi, but fallback
			}
			return qe.summary[i-1].v, nil
		}
	}

	return qe.summary[len(qe.summary)-1].v, nil
}
