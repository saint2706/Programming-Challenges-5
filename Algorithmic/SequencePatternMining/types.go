package main

// Item represents a single symbol in a sequence.
type Item string

// Itemset groups multiple items that occur together.
type Itemset []Item

// Sequence is an ordered list of itemsets.
type Sequence []Itemset

// Pattern represents a discovered frequent sequential pattern along with its support count.
type Pattern struct {
	Sequence Sequence
	Support  int
}

// Clone returns a deep copy of the sequence.
func (s Sequence) Clone() Sequence {
	copySet := make(Sequence, len(s))
	for i, set := range s {
		dup := make(Itemset, len(set))
		copy(dup, set)
		copySet[i] = dup
	}
	return copySet
}
