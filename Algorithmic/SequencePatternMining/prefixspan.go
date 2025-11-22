package main

import (
	"errors"
	"fmt"
	"sort"
	"strings"
)

// MinePrefixSpan discovers frequent sequential patterns in the given database using the PrefixSpan algorithm.
// minSupport is the absolute minimum number of sequences a pattern must appear in to be considered frequent.
func MinePrefixSpan(db []Sequence, minSupport int) ([]Pattern, error) {
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

	var frequentItems []Item
	for item, count := range itemCounts {
		if count >= minSupport {
			frequentItems = append(frequentItems, item)
		}
	}
	sort.Slice(frequentItems, func(i, j int) bool { return frequentItems[i] < frequentItems[j] })

	var results []Pattern
	for _, item := range frequentItems {
		pattern := Sequence{Itemset{item}}
		support := itemCounts[item]
		results = append(results, Pattern{Sequence: pattern.Clone(), Support: support})
		mineProjected(db, pattern, minSupport, &results)
	}

	return results, nil
}

// mineProjected explores deeper extensions for the given prefix.
func mineProjected(db []Sequence, prefix Sequence, minSupport int, results *[]Pattern) {
	iExtensionCounts := make(map[Item]int)
	sExtensionCounts := make(map[Item]int)

	for _, seq := range db {
		embeddings := findEmbeddings(seq, prefix)
		if len(embeddings) == 0 {
			continue
		}
		// Avoid counting a candidate multiple times for the same sequence.
		iSeen := make(map[Item]bool)
		sSeen := make(map[Item]bool)
		for _, emb := range embeddings {
			// itemset extensions: items after the last matched position in the same itemset
			itemset := seq[emb.ItemsetIndex]
			for idx := emb.ItemIndex + 1; idx < len(itemset); idx++ {
				itm := itemset[idx]
				if !iSeen[itm] {
					iExtensionCounts[itm]++
					iSeen[itm] = true
				}
			}
			// sequence extensions: items in following itemsets
			for si := emb.ItemsetIndex + 1; si < len(seq); si++ {
				for _, itm := range seq[si] {
					if !sSeen[itm] {
						sExtensionCounts[itm]++
						sSeen[itm] = true
					}
				}
			}
		}
	}

	// Build and recurse for frequent I-extensions (same itemset)
	var iItems []Item
	for itm, cnt := range iExtensionCounts {
		if cnt >= minSupport {
			iItems = append(iItems, itm)
		}
	}
	sort.Slice(iItems, func(a, b int) bool { return iItems[a] < iItems[b] })
	for _, itm := range iItems {
		next := prefix.Clone()
		last := next[len(next)-1]
		last = append(last, itm)
		next[len(next)-1] = last
		*results = append(*results, Pattern{Sequence: next.Clone(), Support: iExtensionCounts[itm]})
		mineProjected(db, next, minSupport, results)
	}

	// Build and recurse for frequent S-extensions (new itemset)
	var sItems []Item
	for itm, cnt := range sExtensionCounts {
		if cnt >= minSupport {
			sItems = append(sItems, itm)
		}
	}
	sort.Slice(sItems, func(a, b int) bool { return sItems[a] < sItems[b] })
	for _, itm := range sItems {
		next := prefix.Clone()
		next = append(next, Itemset{itm})
		*results = append(*results, Pattern{Sequence: next.Clone(), Support: sExtensionCounts[itm]})
		mineProjected(db, next, minSupport, results)
	}
}

// findEmbeddings returns all possible ways the prefix can be matched inside seq.
type embedding struct {
	ItemsetIndex int
	ItemIndex    int
}

func findEmbeddings(seq Sequence, prefix Sequence) []embedding {
	var embeddings []embedding
	var dfs func(seqIdx int, patIdx int, lastPos int)

	dfs = func(seqIdx int, patIdx int, lastPos int) {
		if patIdx == len(prefix) {
			// Completed pattern; record embedding with last matched position.
			embeddings = append(embeddings, embedding{ItemsetIndex: seqIdx - 1, ItemIndex: lastPos})
			return
		}

		patSet := prefix[patIdx]
		for i := seqIdx; i < len(seq); i++ {
			itemset := seq[i]
			pos := matchItemset(itemset, patSet, 0)
			if pos >= 0 {
				dfs(i+1, patIdx+1, pos)
			}
		}
	}

	dfs(0, 0, -1)
	return embeddings
}

// matchItemset checks whether patSet is a subsequence of itemset (respecting order) and returns
// the index of the last matched item in the itemset, or -1 if not matched.
func matchItemset(itemset Itemset, patSet Itemset, start int) int {
	if len(patSet) == 0 {
		return -1
	}
	pos := start
	for _, patItem := range patSet {
		found := -1
		for i := pos; i < len(itemset); i++ {
			if itemset[i] == patItem {
				found = i
				pos = i + 1
				break
			}
		}
		if found == -1 {
			return -1
		}
	}
	return pos - 1
}

// ContainsSequence reports whether the given sequence contains the pattern as a subsequence.
func ContainsSequence(seq Sequence, pattern Sequence) bool {
	return len(findEmbeddings(seq, pattern)) > 0
}

// FormatPattern renders the pattern as a human-readable string, e.g., "<a b><c>".
func FormatPattern(p Sequence) string {
	sets := make([]string, len(p))
	for i, set := range p {
		items := make([]string, len(set))
		for j, itm := range set {
			items[j] = string(itm)
		}
		sort.Strings(items)
		sets[i] = fmt.Sprintf("<%s>", strings.Join(items, " "))
	}
	return strings.Join(sets, "")
}
