package main

import (
	"errors"
	"fmt"
	"sort"
)

// Item represents a knapsack item with multiple weight dimensions.
type Item struct {
	Weights []int `json:"weights"`
	Value   int   `json:"value"`
}

// Solution contains the optimal value and chosen item indices.
type Solution struct {
	Value       int   `json:"value"`
	ChosenItems []int `json:"chosen_items"`
}

const dpStateLimit = 1_000_000

// SolveMultiDimensionalKnapsack computes the optimal solution using exact DP when feasible
// and falls back to a branch-and-bound search for larger capacity spaces.
func SolveMultiDimensionalKnapsack(items []Item, capacity []int) (Solution, error) {
	if len(capacity) == 0 {
		return Solution{}, errors.New("capacity vector is empty")
	}
	for i, c := range capacity {
		if c < 0 {
			return Solution{}, fmt.Errorf("capacity at dimension %d is negative", i)
		}
	}

	if shouldUseDP(capacity) {
		return solveWithDP(items, capacity), nil
	}
	return solveWithBranchAndBound(items, capacity), nil
}

func shouldUseDP(capacity []int) bool {
	product := 1
	for _, c := range capacity {
		product *= (c + 1)
		if product > dpStateLimit {
			return false
		}
	}
	return true
}

type dpState struct {
	value   int
	prevKey string
	itemIdx int
	took    bool
}

func makeKey(vec []int) string {
	// Compact serialization; dimension count is expected to be small.
	b := make([]byte, 0, len(vec)*4)
	for _, v := range vec {
		b = append(b, byte(v>>24), byte(v>>16), byte(v>>8), byte(v))
	}
	return string(b)
}

func parseKey(key string, dims int) []int {
	res := make([]int, dims)
	for i := 0; i < dims; i++ {
		offset := i * 4
		res[i] = int(uint8(key[offset]))<<24 | int(uint8(key[offset+1]))<<16 | int(uint8(key[offset+2]))<<8 | int(uint8(key[offset+3]))
	}
	return res
}

func solveWithDP(items []Item, capacity []int) Solution {
	dims := len(capacity)
	dp := map[string]dpState{
		makeKey(make([]int, dims)): {value: 0, prevKey: "", itemIdx: -1, took: false},
	}

	for idx, item := range items {
		next := make(map[string]dpState, len(dp))
		for key, state := range dp {
			// Keep existing state
			if existing, ok := next[key]; !ok || existing.value < state.value {
				next[key] = state
			}

			// Try taking the item
			used := parseKey(key, dims)
			if fits(used, item.Weights, capacity) {
				candidateUsed := addVectors(used, item.Weights)
				candKey := makeKey(candidateUsed)
				candVal := state.value + item.Value
				if existing, ok := next[candKey]; !ok || candVal > existing.value {
					next[candKey] = dpState{value: candVal, prevKey: key, itemIdx: idx, took: true}
				}
			}
		}
		dp = next
	}

	// Find best terminal state
	var bestKey string
	bestState := dpState{value: -1}
	for key, state := range dp {
		if state.value > bestState.value {
			bestState = state
			bestKey = key
		}
	}

	chosen := reconstruct(dp, bestKey, dims)
	return Solution{Value: bestState.value, ChosenItems: chosen}
}

func fits(used, weights, capacity []int) bool {
	for i, w := range weights {
		if used[i]+w > capacity[i] {
			return false
		}
	}
	return true
}

func addVectors(a, b []int) []int {
	res := make([]int, len(a))
	for i := range a {
		res[i] = a[i] + b[i]
	}
	return res
}

func reconstruct(states map[string]dpState, key string, dims int) []int {
	var chosen []int
	for key != "" {
		state := states[key]
		if state.took {
			chosen = append(chosen, state.itemIdx)
		}
		key = state.prevKey
	}
	sort.Ints(chosen)
	return chosen
}

type indexedItem struct {
	Item
	Index int
	Score float64
}

func solveWithBranchAndBound(items []Item, capacity []int) Solution {
	indexed := make([]indexedItem, len(items))
	for i, it := range items {
		score := 0.0
		for d, w := range it.Weights {
			if capacity[d] == 0 {
				continue
			}
			score += float64(w) / float64(capacity[d])
		}
		if score == 0 {
			indexed[i] = indexedItem{Item: it, Index: i, Score: 0}
		} else {
			indexed[i] = indexedItem{Item: it, Index: i, Score: float64(it.Value) / score}
		}
	}

	sort.Slice(indexed, func(i, j int) bool {
		return indexed[i].Score > indexed[j].Score
	})

	bestValue := 0
	var bestChoice []int
	var dfs func(pos int, remaining []int, value int, chosen []int)

	dfs = func(pos int, remaining []int, value int, chosen []int) {
		if value > bestValue {
			bestValue = value
			bestChoice = append([]int(nil), chosen...)
		}
		if pos >= len(indexed) {
			return
		}
		bound := value + upperBound(indexed[pos:], remaining)
		if bound <= bestValue {
			return
		}

		current := indexed[pos]
		if canFit(current.Weights, remaining) {
			newRemaining := subtractVectors(remaining, current.Weights)
			dfs(pos+1, newRemaining, value+current.Value, append(chosen, current.Index))
		}

		dfs(pos+1, remaining, value, chosen)
	}

	dfs(0, append([]int(nil), capacity...), 0, nil)
	sort.Ints(bestChoice)
	return Solution{Value: bestValue, ChosenItems: bestChoice}
}

func canFit(weights, remaining []int) bool {
	for i, w := range weights {
		if w > remaining[i] {
			return false
		}
	}
	return true
}

func subtractVectors(a, b []int) []int {
	res := make([]int, len(a))
	for i := range a {
		res[i] = a[i] - b[i]
	}
	return res
}

func upperBound(items []indexedItem, remaining []int) int {
	value := 0.0
	capacity := append([]int(nil), remaining...)
	for _, it := range items {
		if canFit(it.Weights, capacity) {
			value += float64(it.Value)
			capacity = subtractVectors(capacity, it.Weights)
		} else {
			fraction := 1.0
			for i, w := range it.Weights {
				if w == 0 {
					continue
				}
				ratio := float64(capacity[i]) / float64(w)
				if ratio < fraction {
					fraction = ratio
				}
			}
			if fraction > 0 {
				value += float64(it.Value) * fraction
			}
			break
		}
	}
	return int(value + 0.5) // round to nearest int for optimistic bound
}
