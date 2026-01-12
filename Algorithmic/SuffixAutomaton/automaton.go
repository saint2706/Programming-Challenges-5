package main

// State represents a node in the Suffix Automaton (DAWG).
type State struct {
	Len  int          // Length of the longest substring ending at this state
	Link int          // Suffix link (index of the state)
	Next map[rune]int // Transitions
}

// SuffixAutomaton encapsulates the automaton logic.
type SuffixAutomaton struct {
	States []*State
	Last   int // Index of the state corresponding to the entire string processed so far
}

// NewSuffixAutomaton creates a new automaton.
func NewSuffixAutomaton() *SuffixAutomaton {
	sa := &SuffixAutomaton{
		States: make([]*State, 0),
		Last:   0,
	}
	// Initial state (root)
	sa.States = append(sa.States, &State{
		Len:  0,
		Link: -1,
		Next: make(map[rune]int),
	})
	return sa
}

// Extend adds a character to the automaton.
func (sa *SuffixAutomaton) Extend(c rune) {
	cur := len(sa.States)
	sa.States = append(sa.States, &State{
		Len:  sa.States[sa.Last].Len + 1,
		Link: 0,
		Next: make(map[rune]int),
	})

	p := sa.Last
	for p != -1 {
		if _, ok := sa.States[p].Next[c]; ok {
			break
		}
		sa.States[p].Next[c] = cur
		p = sa.States[p].Link
	}

	if p == -1 {
		sa.States[cur].Link = 0
	} else {
		q := sa.States[p].Next[c]
		if sa.States[p].Len+1 == sa.States[q].Len {
			sa.States[cur].Link = q
		} else {
			// Clone state q
			clone := len(sa.States)
			sa.States = append(sa.States, &State{
				Len:  sa.States[p].Len + 1,
				Link: sa.States[q].Link,
				Next: make(map[rune]int),
			})
			// Copy transitions
			for k, v := range sa.States[q].Next {
				sa.States[clone].Next[k] = v
			}

			for p != -1 && sa.States[p].Next[c] == q {
				sa.States[p].Next[c] = clone
				p = sa.States[p].Link
			}
			sa.States[q].Link = clone
			sa.States[cur].Link = clone
		}
	}
	sa.Last = cur
}

// Build constructs the automaton from a string.
func (sa *SuffixAutomaton) Build(s string) {
	for _, c := range s {
		sa.Extend(c)
	}
}

// CheckSubstring returns true if the pattern is a substring.
func (sa *SuffixAutomaton) CheckSubstring(pattern string) bool {
	cur := 0
	for _, c := range pattern {
		if next, ok := sa.States[cur].Next[c]; ok {
			cur = next
		} else {
			return false
		}
	}
	return true
}

// LongestCommonSubstring finds the LCS of the automaton's string and another string.
func (sa *SuffixAutomaton) LongestCommonSubstring(s string) string {
	v := 0
	l := 0
	bestLen := 0
	bestEndPos := 0 // end position in 's'

	for i, c := range s {
		for {
			if _, ok := sa.States[v].Next[c]; ok {
				break
			}
			if v == 0 {
				break
			}
			v = sa.States[v].Link
			l = sa.States[v].Len
		}
		if next, ok := sa.States[v].Next[c]; ok {
			v = next
			l++
		}
		if l > bestLen {
			bestLen = l
			bestEndPos = i
		}
	}
	if bestLen == 0 {
		return ""
	}
	return s[bestEndPos-bestLen+1 : bestEndPos+1]
}

// CountOccurrences returns the number of times pattern appears.
// Note: This requires calculating the size of the endpos set for each state.
// Not strictly required for basic "Check Substring" but useful.
// For now, we'll stick to basic substring check.
// If needed, we can add a topological sort and propagate counts up the suffix links.

func (sa *SuffixAutomaton) NumberOfDistinctSubstrings() int64 {
	// Each path from root corresponds to a substring.
	// But actually sum of (len(u) - len(link(u))) over all states u != root gives distinct substrings.
	// Wait, that is equivalent.
	var count int64 = 0
	for i := 1; i < len(sa.States); i++ {
		count += int64(sa.States[i].Len - sa.States[sa.States[i].Link].Len)
	}
	return count
}
