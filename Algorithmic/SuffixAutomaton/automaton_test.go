package main

import (
	"testing"
)

func TestSuffixAutomaton(t *testing.T) {
	sa := NewSuffixAutomaton()
	sa.Build("banana")

	// 1. Check Substring
	patterns := []struct {
		pat  string
		want bool
	}{
		{"ana", true},
		{"nan", true},
		{"banana", true},
		{"apple", false},
		{"bananas", false},
		{"", true}, // empty string is technically a substring? Loop handles it.
	}

	for _, tc := range patterns {
		got := sa.CheckSubstring(tc.pat)
		if got != tc.want {
			t.Errorf("CheckSubstring(%q) = %v, want %v", tc.pat, got, tc.want)
		}
	}

	// 2. Distinct Substrings
	cnt := sa.NumberOfDistinctSubstrings()
	if cnt != 15 {
		t.Errorf("Distinct substrings = %d, want 15", cnt)
	}

	// 3. Longest Common Substring
	// We don't use 'other' explicitly as variable outside

	sa2 := NewSuffixAutomaton()
	sa2.Build("ABABC")
	lcs := sa2.LongestCommonSubstring("BABCA")
	if lcs != "BABC" {
		t.Errorf("LCS(ABABC, BABCA) = %s, want BABC", lcs)
	}
}
