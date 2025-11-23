package main

import (
	"reflect"
	"testing"
)

func TestSuffixArray(t *testing.T) {
	s := "banana"
	// Suffixes:
	// 0 banana
	// 1 anana
	// 2 nana
	// 3 ana
	// 4 na
	// 5 a

	// Sorted:
	// 5 a
	// 3 ana
	// 1 anana
	// 0 banana
	// 4 na
	// 2 nana

	// SA: [5, 3, 1, 0, 4, 2]
	wantSA := []int{5, 3, 1, 0, 4, 2}
	gotSA := SuffixArray(s)

	if !reflect.DeepEqual(gotSA, wantSA) {
		t.Errorf("SuffixArray(%s) = %v, want %v", s, gotSA, wantSA)
	}

	// LCP:
	// 5 a      (lcp=0)
	// 3 ana    (lcp(a, ana)=1 'a')
	// 1 anana  (lcp(ana, anana)=3 'ana')
	// 0 banana (lcp(anana, banana)=0)
	// 4 na     (lcp(banana, na)=0)
	// 2 nana   (lcp(na, nana)=2 'na')

	// LCP: [0, 1, 3, 0, 0, 2]
	wantLCP := []int{0, 1, 3, 0, 0, 2}
	gotLCP := LCPArray(s, gotSA)

	if !reflect.DeepEqual(gotLCP, wantLCP) {
		t.Errorf("LCPArray(%s) = %v, want %v", s, gotLCP, wantLCP)
	}

	// Distinct Substrings
	// banana = 15
	count := NumberOfDistinctSubstrings(s)
	if count != 15 {
		t.Errorf("Distinct(%s) = %d, want 15", s, count)
	}
}

func TestSuffixArraySimple(t *testing.T) {
	s := "abab"
	// 0 abab
	// 1 bab
	// 2 ab
	// 3 b

	// Sorted:
	// 2 ab
	// 0 abab
	// 3 b
	// 1 bab

	wantSA := []int{2, 0, 3, 1}
	gotSA := SuffixArray(s)
	if !reflect.DeepEqual(gotSA, wantSA) {
		t.Errorf("SuffixArray(%s) = %v, want %v", s, gotSA, wantSA)
	}

	// LCP
	// ab, abab -> ab (2)
	// abab, b -> 0
	// b, bab -> b (1)
	// [0, 2, 0, 1]
	wantLCP := []int{0, 2, 0, 1}
	gotLCP := LCPArray(s, gotSA)
	if !reflect.DeepEqual(gotLCP, wantLCP) {
		t.Errorf("LCPArray(%s) = %v, want %v", s, gotLCP, wantLCP)
	}
}
