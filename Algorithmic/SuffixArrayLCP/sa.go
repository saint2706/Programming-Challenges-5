package main

import (
	"sort"
)

// SuffixArray constructs the suffix array of s.
// Returns a slice of indices where sa[i] is the starting index of the i-th lexicographically smallest suffix.
// Complexity: O(N log^2 N) using simple sorting. O(N log N) with prefix doubling.
func SuffixArray(s string) []int {
	n := len(s)
	sa := make([]int, n)
	rank := make([]int, n)
	newRank := make([]int, n)

	for i := 0; i < n; i++ {
		sa[i] = i
		rank[i] = int(s[i])
	}

	// k is the length of the prefix we are comparing
	for k := 1; k < n; k *= 2 {
		compare := func(i, j int) bool {
			if rank[i] != rank[j] {
				return rank[i] < rank[j]
			}
			ri := -1
			if i+k < n {
				ri = rank[i+k]
			}
			rj := -1
			if j+k < n {
				rj = rank[j+k]
			}
			return ri < rj
		}

		sort.Slice(sa, func(i, j int) bool {
			return compare(sa[i], sa[j])
		})

		newRank[sa[0]] = 0
		for i := 1; i < n; i++ {
			if compare(sa[i-1], sa[i]) {
				newRank[sa[i]] = newRank[sa[i-1]] + 1
			} else {
				newRank[sa[i]] = newRank[sa[i-1]]
			}
		}
		copy(rank, newRank)
		if rank[sa[n-1]] == n-1 {
			break
		}
	}
	return sa
}

// LCPArray constructs the Longest Common Prefix array.
// lcp[i] is the length of the common prefix between suffix sa[i] and sa[i-1].
// lcp[0] is undefined (usually 0).
// Uses Kasai's algorithm O(N).
func LCPArray(s string, sa []int) []int {
	n := len(s)
	rank := make([]int, n)
	for i := 0; i < n; i++ {
		rank[sa[i]] = i
	}

	lcp := make([]int, n)
	h := 0
	for i := 0; i < n; i++ {
		if rank[i] > 0 {
			j := sa[rank[i]-1] // Predecessor in SA
			for i+h < n && j+h < n && s[i+h] == s[j+h] {
				h++
			}
			lcp[rank[i]] = h
			if h > 0 {
				h--
			}
		}
	}
	return lcp
}

// NumberOfDistinctSubstrings calculates the number of distinct substrings using SA and LCP.
// Count = sum(len(suffix) - lcp[rank[suffix]])
// = sum( (n - sa[i]) - lcp[i] )
func NumberOfDistinctSubstrings(s string) int64 {
	sa := SuffixArray(s)
	lcp := LCPArray(s, sa)
	n := len(s)
	var count int64 = 0
	for i := 0; i < n; i++ {
		suffixLen := n - sa[i]
		count += int64(suffixLen - lcp[i])
	}
	return count
}
