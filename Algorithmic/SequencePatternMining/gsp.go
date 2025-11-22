package main

import (
	"errors"
	"sort"
)

// MineGSP implements a simple Generalized Sequential Pattern mining algorithm.
// It is less efficient than PrefixSpan but provided as an alternative baseline.
func MineGSP(db []Sequence, minSupport int) ([]Pattern, error) {
	if minSupport < 1 {
		return nil, errors.New("minSupport must be at least 1")
	}

	itemCounts := make(map[Item]int)
	for _, seq := range db {
		seen := make(map[Item]bool)
		for _, set := range seq {
			for _, item := range set {
				if !seen[item] {
					itemCounts[item]++
					seen[item] = true
				}
			}
		}
	}

	var items []Item
	for item, cnt := range itemCounts {
		if cnt >= minSupport {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i] < items[j] })

	var results []Pattern
	var level []Sequence
	for _, itm := range items {
		pattern := Sequence{Itemset{itm}}
		results = append(results, Pattern{Sequence: pattern, Support: itemCounts[itm]})
		level = append(level, pattern)
	}

	seen := make(map[string]bool)
	for len(level) > 0 {
		var candidates []Sequence
		for _, pat := range level {
			for _, itm := range items {
				// Sequence extension
				candSeq := pat.Clone()
				candSeq = append(candSeq, Itemset{itm})
				key := FormatPattern(candSeq)
				if !seen[key] {
					candidates = append(candidates, candSeq)
					seen[key] = true
				}
				// Itemset extension
				last := append(Itemset{}, pat[len(pat)-1]...)
				last = append(last, itm)
				candItemset := pat.Clone()
				candItemset[len(candItemset)-1] = last
				key = FormatPattern(candItemset)
				if !seen[key] {
					candidates = append(candidates, candItemset)
					seen[key] = true
				}
			}
		}

		level = nil
		for _, cand := range candidates {
			support := 0
			for _, seq := range db {
				if ContainsSequence(seq, cand) {
					support++
				}
			}
			if support >= minSupport {
				results = append(results, Pattern{Sequence: cand, Support: support})
				level = append(level, cand)
			}
		}
	}

	return results, nil
}
